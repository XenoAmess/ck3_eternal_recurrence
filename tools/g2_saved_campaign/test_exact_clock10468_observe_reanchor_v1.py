"""Actual frozen Queue/dispatcher AST, closed inputs, injected RAM I/O/session.

No Game/process/pipe/desktop/Driver/SAVE call and no runtime filesystem write.
Successful SDK response bodies below are software fixtures, never observations.
"""
import ast
import copy
from contextlib import nullcontext
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import exact_clock10468_observe_reanchor_v1 as o

sys.path.insert(0, str(o.BASE / "sdk-v20261019-candidate/src17"))


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def functions(raw, names, namespace, *, last=()):
    tree = ast.parse(raw)
    for name in names:
        matches = sorted((node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name),
            key=lambda node: node.lineno)
        node = copy.deepcopy(matches[-1] if name in last else matches[0])
        node.decorator_list = []
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                     namespace["__file__"], "exec"), namespace)


class Ram:
    def __init__(self):
        self.files, self.writes, self.fail_state = {}, [], False

    def raw(self, path, limit=262144):
        path = Path(path)
        raw = self.files[path] if path in self.files else ORIGINAL_RAW(path, limit)
        if len(raw) > limit:
            raise ValueError("fixture read bound")
        return raw

    def atomic(self, path, value, *, replace=False, limit=64*1024**2):
        path, payload = Path(path), encoded(value)
        if len(payload) > limit:
            raise ValueError("fixture write bound")
        if path in self.files and not replace:
            raise FileExistsError(path)
        if self.fail_state and path.name == "ROOT-CUMULATIVE-LOOP-STATE.json":
            raise OSError("injected second-file metadata write failure")
        self.files[path] = payload
        self.writes.append(path)

    def read(self, path, limit=262144):
        return json.loads(self.raw(path, limit))

    def exists(self, path):
        return Path(path) in self.files or Path(path).exists()


ORIGINAL_RAW = o._raw


def build():
    ram = Ram()
    state = json.loads(ORIGINAL_RAW(o.F97 / "state.json"))
    gov = json.loads(ORIGINAL_RAW(o.F97 / "gov.json"))
    auto = json.loads(ORIGINAL_RAW(o.F97 / "AUTO.json"))
    for leaf, source in (("ROOT-CUMULATIVE-LOOP-STATE.json", "state.json"),
                         ("ROOT-GOVERNANCE-RESULT-STATE.json", "gov.json")):
        ram.files[o.T / "p37-queue" / leaf] = ORIGINAL_RAW(o.F97 / source)
    ram.files[o.T / "p37-responses/10468-1-result.json"] = ORIGINAL_RAW(o.F97 / "AUTO.json")
    ram.files[o.T / "NEXT-SEQUENCE-P37.json"] = encoded({"next_sequence": 10469})
    namespace = {"__file__": str(o.T / "root_p37c20_sdk_queue.py"),
        "Path": Path, "json": json, "hashlib": hashlib, "Q": o.T / "p37-queue", "N": o.T,
        "INBOX": o.T / "p37-requests", "OUTBOX": o.T / "p37-responses",
        "SEMANTIC": "ck3_take_semantic_snapshot_private_v1", "REPLY_RESERVE": 64*1024**2,
        "atomic": ram.atomic, "read": ram.read, "now": lambda: datetime.now(timezone.utc),
        "_control_call_v1": lambda _name, fn, *a, **k: fn(*a, **k),
        "_control_span_v1": lambda _name: nullcontext()}
    queue_raw = ORIGINAL_RAW(o.T / "root_p37c20_sdk_queue.py", 1024**2)
    if hashlib.sha256(queue_raw).hexdigest() != o.QUEUE_SHA:
        raise ValueError("actual Queue pin differs")
    functions(queue_raw, ("decoded", "frame", "consume_sequence", "persist_loop_state",
                         "recover_partial_life_advance"), namespace, last=("recover_partial_life_advance",))
    Queue = type("ActualInheritedControlFixture", (), {name: namespace[name] for name in
        ("consume_sequence", "persist_loop_state", "recover_partial_life_advance")})
    q = Queue()
    q.full_loop_state = copy.deepcopy(state)
    q.governance_result_state = copy.deepcopy(gov["state"])
    q.lifestyle_pending_focus = gov["pending_focus"]
    q.result_classifier_pin = gov["classifier"]
    q.expected_lifecycle_binding = state["actual_saved_checkpoint"]["succession_lifecycle"]
    q.launch = {"pid": o.GAME, "pipe": r"\\.\pipe\xar-g2-robert30-v20261019-campaign01"}
    q.job = {"game_creation_filetime": o.BIRTH}
    q.halted = {"request": auto["request"], "row": auto,
                "response": str(o.T / "p37-responses/10468-1-result.json")}
    q.current_attempt = copy.deepcopy(q.halted)
    q.next_sequence, q.held_control, q.guards = 10469, None, 0
    def guard(*_a, **_k):
        q.guards += 1
    q.guard, q.call_budget = guard, lambda _tool: 10
    q.semantic = {"untrusted_old": True}
    dispatcher = ModuleType("root_p37_known_pause_recovery_control")
    dispatcher.__dict__["__file__"] = str(o.T / "root_p37_known_pause_recovery_control.py")
    dispatcher.__dict__["process_birth_filetime"] = lambda _pid: o.BIRTH
    original_dispatcher = ORIGINAL_RAW(o.T / "root_p37_known_pause_recovery_control.py")
    transformed = o.transform_dispatcher_v1(original_dispatcher)
    functions(transformed, ("recover",), dispatcher.__dict__)
    body = {"snapshot_id": "native:4370", "revision": 5, "native_revision": 4370,
            "date_raw": o.DATE, "paused": True, "map_ready": True,
            "played_character": {"alive": True, "character_id": 40526},
            "episode_run_id": o.EPISODE, "one_life_terminal": False,
            "one_life_terminal_reason": None,
            "succession_lifecycle": q.expected_lifecycle_binding,
            "campaign_goal": state["campaign_goal_anchor"],
            "active_event": {"instance_id": 111, "source": "software fixture new event"},
            "pending_character_interaction": None, "player_armies": [{"army_id": 23}],
            "active_wars": [{"war_id": 12}], "exclusive_modal": {"unknown": True},
            "diagnostics": {"bridge_pid": o.GAME, "connection_generation": 4,
                "pipe_name": q.launch["pipe"], "hello": {"pid": o.GAME,
                    "connection_generation": 4, "ck3_build_match": True,
                    "game_adapter_status": "ready", "game_adapter_id": "ck3-1.20.0.4-msvc-x64"}}}
    return q, ram, dispatcher, body, state, gov


class Session:
    def __init__(self, q, body, *, status_error=False, semantic_error=False):
        self.q, self.body = q, body
        self.status_error, self.semantic_error = status_error, semantic_error
        self.calls = []

    async def call_tool(self, tool, arguments, **kwargs):
        if self.q.halted is None:
            raise AssertionError("halt cleared before observation")
        self.calls.append((tool, copy.deepcopy(arguments)))
        if tool == "ck3_execute_step":
            if arguments != {"step": o.STATUS_STEP}:
                raise AssertionError("arbitrary or replayed step")
            result = {"is_error": self.status_error, "result_type": "complete",
                      "structured_content": None if self.status_error else {
                          "step": o.STATUS_STEP, "accepted": True,
                          "tactical_daily_sentinel": {"generation": 123, "state": "idle"}}}
        else:
            if tool != "ck3_take_semantic_snapshot_private_v1" or arguments:
                raise AssertionError("nonreadonly tool")
            if self.semantic_error:
                raise TimeoutError("software fixture semantic unavailable; never repeat")
            result = {"is_error": False, "result_type": "complete", "structured_content": self.body}
        return SimpleNamespace(model_dump=lambda **_kwargs: copy.deepcopy(result))


class Qualification(unittest.IsolatedAsyncioTestCase):
    async def invoke(self, q, ram, dispatcher, session):
        request = {"sequence": 10469, "command": "recover_partial_life_advance",
                   "arguments": {"recovery_kind": o.KIND}}
        with patch.object(o, "_raw", ram.raw), patch.object(o, "_exists", ram.exists), \
                patch.object(Path, "read_bytes", lambda path: ram.raw(path, 2*1024**2)), patch.dict(sys.modules, {
            "root_p37_known_pause_recovery_control": dispatcher,
            "root_p37c20_exact_clock10468_reconcile": o}):
            return await q.recover_partial_life_advance(session, request,
                o.T / "p37-requests/10469-1-result.json")

    async def test_actual_lazy_entry_observes_and_reanchors_without_credit(self):
        q, ram, dispatcher, body, state, gov = build()
        session = Session(q, body)
        result = await self.invoke(q, ram, dispatcher, session)
        self.assertEqual(result["status"], "unknown_failed_clock_observed_and_reanchored", result)
        self.assertEqual(session.calls, [("ck3_execute_step", {"step": o.STATUS_STEP}),
            ("ck3_take_semantic_snapshot_private_v1", {})])
        self.assertEqual(q.next_sequence, 10472)
        self.assertIsNone(q.halted)
        self.assertEqual(q.full_loop_state["counts"], state["counts"])
        self.assertEqual(q.full_loop_state["completed_cycles"], 4752)
        self.assertTrue(q.full_loop_state["checkpoint_dirty_since_save"])
        self.assertEqual(q.full_loop_state["actual_saved_checkpoint"], state["actual_saved_checkpoint"])
        self.assertEqual(q.full_loop_state["before"]["date_raw"], o.DATE)
        self.assertIsNone(q.full_loop_state["pending_cycle"])
        self.assertEqual(ram.read(o.T / "p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json"), {**gov, "pending_cycle": None})
        self.assertEqual(q.semantic, body)  # New UI/war/army fields were not discarded.
        audit = ram.read(o.T / "p37-queue/EXACT-CLOCK10468-OBSERVE-10469.json")
        self.assertEqual(audit["cleanup_cancel_result"], "unknown")
        self.assertEqual(audit["sentinel_stop_validation"], "not_reached")
        self.assertEqual(audit["failed_cycle_credit"], 0)
        self.assertEqual(audit["current_slot_readback"]["generation"], 123)
        self.assertLess(sum(len(b) for p, b in ram.files.items() if p in ram.writes), 524288)
        with self.assertRaises(ValueError):
            await self.invoke(q, ram, dispatcher, session)
        self.assertEqual(len(session.calls), 2)

    async def test_status_refusal_is_preserved_unknown_and_not_retried(self):
        q, ram, dispatcher, body, _state, _gov = build()
        session = Session(q, body, status_error=True)
        result = await self.invoke(q, ram, dispatcher, session)
        self.assertEqual(result["status"], "unknown_failed_clock_observed_and_reanchored", result)
        self.assertEqual(len(session.calls), 2)
        audit = ram.read(o.T / "p37-queue/EXACT-CLOCK10468-OBSERVE-10469.json")
        self.assertFalse(audit["current_slot_observed"])
        self.assertTrue(ram.read(o.T / "p37-responses/10470-1-result.json")["result"]["is_error"])

    async def test_fresh_predicate_or_semantic_failure_keeps_halt_and_pending(self):
        for bad in ("actor", "date", "goal", "connection", "running", "semantic_error"):
            with self.subTest(bad=bad):
                q, ram, dispatcher, body, state, gov = build()
                original = q.halted
                if bad == "actor": body["played_character"]["character_id"] += 1
                elif bad == "date": body["date_raw"] -= 24
                elif bad == "goal": body["campaign_goal"] = {}
                elif bad == "connection": body["diagnostics"]["connection_generation"] = 5
                elif bad == "running": body["paused"] = False
                session = Session(q, body, semantic_error=bad == "semantic_error")
                result = await self.invoke(q, ram, dispatcher, session)
                self.assertEqual(result["status"], "F97_observe_reanchor_failed_halt_retained")
                self.assertIs(q.halted, original)
                self.assertEqual(q.full_loop_state, state)
                self.assertEqual(ram.read(o.T / "p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json"), gov)
                self.assertEqual(len(session.calls), 2)
                self.assertEqual(q.next_sequence, 10472)

    async def test_old_state_drift_rejects_before_any_read_or_write(self):
        q, ram, dispatcher, body, _state, _gov = build()
        q.full_loop_state["completed_cycles"] += 1
        session = Session(q, body)
        with self.assertRaises(ValueError):
            await self.invoke(q, ram, dispatcher, session)
        self.assertEqual(session.calls, [])
        self.assertEqual(ram.writes, [])
        self.assertEqual(q.next_sequence, 10469)

    async def test_second_metadata_file_failure_is_not_claimed_atomic(self):
        q, ram, dispatcher, body, state, _gov = build()
        ram.fail_state = True
        original = q.halted
        session = Session(q, body)
        result = await self.invoke(q, ram, dispatcher, session)
        self.assertIs(q.halted, original)
        self.assertEqual(q.full_loop_state, state)
        self.assertTrue(result["metadata_may_be_partially_committed"])
        self.assertEqual(len(session.calls), 2)
        self.assertIsNone(ram.read(o.T / "p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json")["pending_cycle"])
        self.assertEqual(ram.read(o.T / "p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json"), state)


if __name__ == "__main__":
    unittest.main(verbosity=2)
