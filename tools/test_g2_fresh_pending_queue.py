"""Exercise Root's actual external queue recovery with memory SDK replies.

The external source paths are explicit CLI inputs, never CI machine assumptions.
No FreshQueue constructor, supervisor main, stdio client, Game or process API runs.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


QUEUE_SOURCE: Path | None = None
SUPERVISOR_SOURCE: Path | None = None
ARTIFACT_ROOT: Path | None = None


def load_source(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load explicit external source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MemoryResult:
    def __init__(self, value):
        self.value = deepcopy(value)

    def model_dump(self, *, mode):
        if mode != "json":
            raise RuntimeError("fixture expects production JSON serialization")
        return deepcopy(self.value)


class MemorySession:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    async def call_tool(self, tool, arguments, *, read_timeout_seconds):
        self.calls.append((tool, deepcopy(arguments), read_timeout_seconds))
        if not self.replies:
            raise RuntimeError("unexpected SDK call: " + tool)
        expected, value = self.replies.pop(0)
        if tool != expected:
            raise RuntimeError("unexpected SDK tool: " + tool + "; wanted " + expected)
        if isinstance(value, Exception):
            raise value
        return MemoryResult(value)


def sdk_body(value):
    return {"is_error": False, "structured_content": deepcopy(value)}


class FreshPendingQueueIntegrationTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        if QUEUE_SOURCE is None or SUPERVISOR_SOURCE is None or ARTIFACT_ROOT is None:
            raise unittest.SkipTest("explicit external queue/supervisor/artifact paths required")
        cls.queue_module = load_source(QUEUE_SOURCE, "g2_pending_queue_integrated_fixture")
        cls.core = load_source(QUEUE_SOURCE.with_name("root_pending_declaration_recovery.py"),
                               "root_pending_declaration_recovery")
        cls.supervisor = load_source(SUPERVISOR_SOURCE, "g2_pending_supervisor_integrated_fixture")

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory(
            prefix="queue-case-", dir=ARTIFACT_ROOT)))
        self.stack.enter_context(patch.dict(sys.modules,
            {"root_pending_declaration_recovery": self.core}))
        self.paths = {"N": self.root, "R": self.root.parent,
            "Q": self.root / "sdk-session01", "INBOX": self.root / "requests",
            "OUTBOX": self.root / "responses"}
        for name, value in self.paths.items():
            self.stack.enter_context(patch.object(self.queue_module, name, value))
            if name != "R":
                value.mkdir(exist_ok=True)
        (self.root / "display-responses").mkdir()
        self.stack.enter_context(patch.object(self.supervisor, "N", self.root))
        self.queue = self.queue_module.FreshQueue.__new__(self.queue_module.FreshQueue)
        self.queue.next_sequence = 1
        self.queue.frontend_done = 3
        self.queue.initial_save = {"fixture": "existing actual initial-save gate bypass"}
        self.queue.loop_count = 1
        self.queue.held_control = None
        self.queue.halted = None
        self.queue.current_attempt = None
        self.queue.semantic = {"fixture": "discarded after available collection"}
        self.queue.deadline = datetime.now(timezone.utc) + timedelta(minutes=5)
        self.queue.guard = lambda **kwargs: None
        self.queue.check_after = lambda *args: None
        self.queue.launch = {"pid": 4242, "creation_date": "memory-fixture-generation"}
        self.binding = {"snapshot_id": "native:40", "revision": 9,
            "native_revision": 40, "paused": True, "map_ready": True,
            "bridge_pid": 4242, "connection_generation": 3,
            "episode_run_id": "ordinary-memory-fixture", "date_raw": 53175817,
            "player_character_id": 29829}
        self.retained = {"request_id": "original-native-enumeration-17",
            "step": "query-declarable-wars", "status": "pending",
            "binding": deepcopy(self.binding), "timeout_seconds": 120.0}
        self.diagnostics = {"bridge_pid": 4242,
            "pending_declaration_query": deepcopy(self.retained)}
        self.semantic = {"paused": True, "map_ready": True, "revision": 9,
            "played_character": {"character_id": 29829, "alive": True},
            "diagnostics": {"bridge_pid": 4242}}
        self.collected = {"schema": "ck3-declarable-war-result-collection-v1",
            "request_id": self.retained["request_id"], "original_binding": deepcopy(self.binding),
            "current_binding": deepcopy(self.binding), "native_resubmitted": False,
            "cache_restored": True, "status": "available",
            "declaration_result": {"query_sequence": 1, "declarable_wars": []},
            "native_result_frame": {"request_id": self.retained["request_id"], "ok": True}}
        self.original_request = None
        self.original_response = None
        self.original_bytes = None

    def inbox(self, request):
        path = self.paths["INBOX"] / f"{request['sequence']:04d}-1-result.json"
        self.queue_module.atomic(path, request, limit=16384)
        return path

    async def original_failure(self, *, tool=None, step="query-declarable-wars", client_error=False):
        tool = tool or self.queue_module.AUTO
        request = {"sequence": 1, "tool": tool, "arguments": {}}
        path = self.inbox(request)
        plan = {"source": "actual GameplayBridgeService.before_submit callback",
            "game_pid": 4242, "game_creation_date": self.queue.launch["creation_date"],
            "request": {"tool": "root_before_auto_turn_submit", "parent_sequence": 1},
            "result": {"structured_content": {"selected_step": step,
                "plan": {"selected_step": step}, "revision": 9, "snapshot_id": "native:40"}}}
        self.queue_module.atomic(self.paths["OUTBOX"] / "0001-0-plan.json", plan, limit=16384)
        if client_error:
            reply = TimeoutError("memory client timeout; actual command outcome unknown")
        else:
            text = "memory original SDK error"
            if tool == self.queue_module.AUTO and step == "query-declarable-wars":
                text += "; retained_declaration_query=" + json.dumps(self.retained, sort_keys=True)
            reply = {"is_error": True, "content": [{"type": "text", "text": text}]}
        session = MemorySession([(tool, reply)])
        # Permit each original error fixture; later halted admission uses the
        # actual production check_before method, with its unrelated state ready.
        with patch.object(self.queue, "check_before", lambda *args: None):
            with self.assertRaises(RuntimeError) as raised:
                await self.queue.call(session, request, path)
        self.original_request = request
        self.original_response = self.paths["OUTBOX"] / path.name
        self.original_bytes = self.original_response.read_bytes()
        self.original_session = session
        self.queue.halt_request(raised.exception, request, path)
        self.assertEqual(self.original_response.read_bytes(), self.original_bytes)
        self.assertEqual(len(session.calls), 1)
        self.assertEqual(self.queue.next_sequence, 2)
        self.assertIsNotNone(self.queue.halted)
        self.assertTrue((self.paths["Q"] / "ROOT-REQUEST-HALTED-0001.json").is_file())
        self.assertTrue((self.root / "ROOT-CURRENT-HALT.json").is_file())
        self.assertFalse((self.paths["Q"] / "ROOT-QUEUE-HALTED.json").exists())
        self.assertFalse((self.paths["Q"] / "ROOT-QUEUE-CLOSED.json").exists())
        self.assertFalse(self.supervisor.sdk_queue_terminal_marker())
        return session

    def same_session(self, replies):
        self.original_session.replies.extend(replies)
        return self.original_session

    async def collect(self, session):
        self.assertIs(session, self.original_session)
        request = {"sequence": self.queue.next_sequence,
            "command": "collect_original_declarable", "arguments": {}}
        path = self.inbox(request)
        result = await self.queue.collect_original(session, request, path)
        self.assertEqual(self.original_response.read_bytes(), self.original_bytes)
        self.assertFalse(self.supervisor.sdk_queue_terminal_marker())
        return result

    def recovery_replies(self, *, collector=None):
        return [(self.core.DIAGNOSTICS, sdk_body(self.diagnostics)),
                (self.core.SEMANTIC, sdk_body(self.semantic)),
                (self.core.COLLECT, sdk_body(self.collected) if collector is None else collector)]

    async def assert_halted_blocks_action(self, session):
        before = len(session.calls)
        request = {"sequence": self.queue.next_sequence,
            "tool": self.queue_module.AUTO, "arguments": {}}
        path = self.inbox(request)
        with self.assertRaisesRegex(RuntimeError, "remains halted"):
            await self.queue.call(session, request, path)
        self.assertEqual(len(session.calls), before)
        self.assertEqual(self.original_response.read_bytes(), self.original_bytes)

    async def test_available_keeps_original_bytes_and_accepts_only_new_normal_request(self):
        await self.original_failure()
        session = self.same_session(self.recovery_replies() + [(self.queue_module.AUTO,
            sdk_body({"status": "executed", "result": {"accepted": True},
                "plan": {"selected_step": "memory-next-normal-plan"}}))])
        result = await self.collect(session)
        self.assertTrue(result["can_replan"])
        self.assertIsNone(self.queue.halted)
        self.assertEqual(self.queue.next_sequence, 6)
        self.assertEqual(self.queue.frontend_done, 3)
        self.assertEqual(self.queue.loop_count, 1)
        self.assertIsNone(self.queue.semantic)
        self.assertEqual([(tool, args) for tool, args, _ in session.calls], [
            (self.queue_module.AUTO, {}),
            (self.core.DIAGNOSTICS, {}), (self.core.SEMANTIC, {}),
            (self.core.COLLECT, {"request_id": self.retained["request_id"], "expected_revision": 9})])
        # Reusing the old request fails before the fake SDK is called.
        with self.assertRaises(ValueError):
            await self.queue.call(session, self.original_request,
                self.paths["INBOX"] / "0001-1-result.json")
        self.assertEqual(len(session.calls), 4)
        next_request = {"sequence": 6, "tool": self.queue_module.AUTO, "arguments": {}}
        await self.queue.call(session, next_request, self.inbox(next_request))
        self.assertEqual(self.queue.next_sequence, 7)
        self.assertEqual([tool for tool, _, _ in session.calls], [
            self.queue_module.AUTO, self.core.DIAGNOSTICS, self.core.SEMANTIC,
            self.core.COLLECT, self.queue_module.AUTO])
        for number in range(1, 7):
            self.assertTrue((self.paths["INBOX"] / f"{number:04d}-1-result.json").is_file())
            self.assertTrue((self.paths["OUTBOX"] / f"{number:04d}-1-result.json").is_file())
        self.assertEqual(self.original_response.read_bytes(), self.original_bytes)

    async def test_pending_keeps_halt_without_polling_or_query_replay(self):
        await self.original_failure()
        self.collected.update(status="pending", cache_restored=False)
        session = self.same_session(self.recovery_replies())
        result = await self.collect(session)
        self.assertEqual(result["status"], "halted_pending")
        self.assertFalse(result["can_replan"])
        self.assertEqual(len(session.calls), 4)
        await self.assert_halted_blocks_action(session)

    async def test_stale_passes_actual_current_revision_and_stays_halted(self):
        await self.original_failure()
        self.semantic["revision"] = 10
        self.collected.update(status="stale", cache_restored=False, current_binding={})
        session = self.same_session(self.recovery_replies())
        result = await self.collect(session)
        self.assertEqual(result["status"], "halted_stale")
        self.assertEqual(session.calls[-1][1],
            {"request_id": self.retained["request_id"], "expected_revision": 10})
        await self.assert_halted_blocks_action(session)

    async def test_malformed_collector_result_is_retained_and_stays_halted(self):
        await self.original_failure()
        self.collected.pop("request_id")
        session = self.same_session(self.recovery_replies())
        result = await self.collect(session)
        self.assertEqual(result["status"], "halted_collection_unavailable")
        raw = json.loads((self.paths["OUTBOX"] / "0005-1-result.json").read_text(encoding="utf-8"))
        self.assertNotIn("request_id", raw["result"]["structured_content"])
        await self.assert_halted_blocks_action(session)

    async def test_original_start_unknown_cannot_enter_collector(self):
        await self.original_failure(tool=self.queue_module.FRONTEND[2], step="frontend-start")
        session = self.same_session([])
        result = await self.collect(session)
        self.assertFalse(result["can_replan"])
        self.assertEqual(len(session.calls), 1)
        await self.assert_halted_blocks_action(session)

    async def test_original_close_unknown_cannot_enter_collector(self):
        await self.original_failure(step="close-war-declared-overview-v1")
        session = self.same_session([])
        result = await self.collect(session)
        self.assertFalse(result["can_replan"])
        self.assertEqual(len(session.calls), 1)
        await self.assert_halted_blocks_action(session)

    async def test_original_save_unknown_cannot_enter_collector(self):
        await self.original_failure(tool=self.queue_module.SAVE, step="save-checkpoint")
        session = self.same_session([])
        result = await self.collect(session)
        self.assertFalse(result["can_replan"])
        self.assertEqual(len(session.calls), 1)
        await self.assert_halted_blocks_action(session)

    async def test_client_timeout_keeps_unknown_without_recovery_calls(self):
        await self.original_failure(client_error=True)
        session = self.same_session([])
        result = await self.collect(session)
        self.assertFalse(result["can_replan"])
        self.assertEqual(len(session.calls), 1)
        await self.assert_halted_blocks_action(session)

    async def test_only_fatal_or_closed_marker_not_recoverable_halt_requests_supervisor_stop(self):
        await self.original_failure()
        self.assertFalse(self.supervisor.sdk_queue_terminal_marker())
        fatal = self.paths["Q"] / "ROOT-QUEUE-HALTED.json"
        self.queue_module.atomic(fatal, {"fixture": "fatal queue terminal state"}, limit=16384)
        self.assertTrue(self.supervisor.sdk_queue_terminal_marker())
        fatal.unlink()
        self.assertFalse(self.supervisor.sdk_queue_terminal_marker())
        self.queue_module.atomic(self.paths["Q"] / "ROOT-QUEUE-CLOSED.json",
            {"fixture": "actual queue context closed marker"}, limit=16384)
        self.assertTrue(self.supervisor.sdk_queue_terminal_marker())


def main():
    global QUEUE_SOURCE, SUPERVISOR_SOURCE, ARTIFACT_ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue-source", type=Path, required=True)
    parser.add_argument("--supervisor-source", type=Path)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    QUEUE_SOURCE = args.queue_source.resolve(strict=True)
    SUPERVISOR_SOURCE = (args.supervisor_source or
        QUEUE_SOURCE.with_name("root_fresh_supervisor.py")).resolve(strict=True)
    ARTIFACT_ROOT = args.artifacts.resolve()
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FreshPendingQueueIntegrationTests)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    log = stream.getvalue().encode("utf-8")
    if len(log) > 1024**2:
        raise RuntimeError("focused fixture log exceeded 1 MiB")
    (ARTIFACT_ROOT / "tests.log").write_bytes(log)
    sources = (QUEUE_SOURCE, SUPERVISOR_SOURCE,
        QUEUE_SOURCE.with_name("root_pending_declaration_recovery.py"), Path(__file__).resolve())
    receipt = {"status": "GREEN" if result.wasSuccessful() else "RED",
        "tests_run": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skipped": len(result.skipped),
        "elapsed_seconds": time.monotonic() - started,
        "actual_queue_methods_executed": ["call", "halt_request", "collect_original",
            "recovery_read", "consume_sequence", "check_before"],
        "actual_supervisor_method_executed": "sdk_queue_terminal_marker",
        "sdk_replies": "memory fixture only", "SDK_or_Game_process_started": False,
        "sources": [{"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sources]}
    (ARTIFACT_ROOT / "result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, separators=(",", ":")))
    if not result.wasSuccessful():
        print(stream.getvalue())
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
