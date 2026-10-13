"""Focused fake-session checks for the fresh queue's two research reads.

The supplied queue is imported without constructor/preflight or main. Its
real call path retains two typed reads through one caller-owned fake session;
no Game, native pipe, SDK application, Steam or window is accessed.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from test_g2_fresh_queue_lifecycle import OUTPUT_LIMIT, _storage_check


QUEUE_HELPER_PATH: Path | None = None
RECEIPT_ROOT: Path | None = None


class _FakeResult:
    def __init__(self, body: dict) -> None:
        self.body = body

    def model_dump(self, *, mode: str) -> dict:
        if mode != "json":
            raise ValueError("the real queue must request JSON result serialization")
        return {"is_error": False, "structured_content": copy.deepcopy(self.body)}


class _RetainedFakeSession:
    def __init__(self, module) -> None:
        self.module = module
        self.calls = []

    async def call_tool(self, tool, arguments, *, read_timeout_seconds):
        if tool not in self.module.READONLY_RESEARCH:
            raise AssertionError("research requested a gameplay/action tool")
        if not 0 < read_timeout_seconds <= 300:
            raise AssertionError("the existing bounded call timeout changed")
        self.calls.append((tool, copy.deepcopy(arguments)))
        body = {"status": "available", "fixture_read_only": True}
        if tool == self.module.NODE_IDENTITY:
            body.update({"declaration_id": arguments["declaration_id"],
                         "participant_coverage_complete": False,
                         "war_permission": False})
        return _FakeResult(body)


class FreshReadonlyResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if QUEUE_HELPER_PATH is None:
            raise RuntimeError("an explicit --queue-helper is required")
        spec = importlib.util.spec_from_file_location(
            "g2_fresh_readonly_research_under_test", QUEUE_HELPER_PATH
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load the selected queue helper")
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.module
        spec.loader.exec_module(cls.module)

    def setUp(self) -> None:
        self.queue = self.module.FreshQueue.__new__(self.module.FreshQueue)
        self.queue.frontend_done = 3
        self.queue.initial_save = {"status": "saved", "fixture_only": True}
        self.queue.semantic = {"revision": 41, "fixture_only": True}
        self.queue.next_sequence = 1
        self.queue.loop_count = 0
        self.queue.halted = None
        self.queue.current_attempt = None
        self.queue.deadline = datetime.now(timezone.utc) + timedelta(minutes=5)
        self.session = _RetainedFakeSession(self.module)

    def arguments(self, tool: str, revision: int = 41) -> dict:
        result = {"expected_revision": revision}
        if tool == self.module.NODE_IDENTITY:
            result["declaration_id"] = "fixture-current-declaration"
        return result

    def test_declarable_accepts_exact_typed_revision_bounds(self) -> None:
        for revision in (1, 2**64 - 1):
            with self.subTest(revision=revision):
                self.queue.check_before(
                    self.module.DECLARABLE, self.arguments(self.module.DECLARABLE, revision)
                )
        self.assertEqual(self.session.calls, [])
        self.assertEqual(self.queue.next_sequence, 1)

    def test_node_accepts_bounded_identity_and_typed_revision(self) -> None:
        for identity in ("x", "x" * 1024):
            with self.subTest(identity_length=len(identity)):
                arguments = self.arguments(self.module.NODE_IDENTITY, 2**64 - 1)
                arguments["declaration_id"] = identity
                self.queue.check_before(self.module.NODE_IDENTITY, arguments)
        self.assertEqual(self.session.calls, [])

    def test_both_reads_reject_untyped_revision_and_extra_arguments(self) -> None:
        for tool in self.module.READONLY_RESEARCH:
            for revision in (True, False, 0, -1, 2**64, 1.0, "1", None):
                with self.subTest(tool=tool, revision=revision):
                    with self.assertRaises(ValueError):
                        self.queue.check_before(tool, self.arguments(tool, revision))
            for change in ("missing_revision", "extra_argument"):
                with self.subTest(tool=tool, change=change):
                    arguments = self.arguments(tool)
                    if change == "missing_revision":
                        del arguments["expected_revision"]
                    else:
                        arguments["unused"] = True
                    with self.assertRaises(ValueError):
                        self.queue.check_before(tool, arguments)
        self.assertEqual(self.session.calls, [])

    def test_node_rejects_missing_untyped_or_oversized_identity(self) -> None:
        for identity in (None, True, 1, b"id", "", "x" * 1025):
            with self.subTest(identity_type=type(identity).__name__, identity_length=(
                len(identity) if isinstance(identity, (str, bytes)) else None
            )):
                arguments = self.arguments(self.module.NODE_IDENTITY)
                arguments["declaration_id"] = identity
                with self.assertRaises(ValueError):
                    self.queue.check_before(self.module.NODE_IDENTITY, arguments)
        with self.assertRaises(ValueError):
            self.queue.check_before(self.module.NODE_IDENTITY, {"expected_revision": 41})
        self.assertEqual(self.session.calls, [])

    def test_both_reads_refuse_before_frontend_completion(self) -> None:
        for completed in (0, 1, 2):
            self.queue.frontend_done = completed
            for tool in self.module.READONLY_RESEARCH:
                with self.subTest(completed=completed, tool=tool):
                    with self.assertRaises(ValueError):
                        self.queue.check_before(tool, self.arguments(tool))
        self.assertEqual(self.session.calls, [])

    def test_both_reads_refuse_before_initial_save(self) -> None:
        self.queue.initial_save = None
        for tool in self.module.READONLY_RESEARCH:
            with self.subTest(tool=tool):
                with self.assertRaises(ValueError):
                    self.queue.check_before(tool, self.arguments(tool))
        self.assertEqual(self.session.calls, [])

    def test_halted_queue_refuses_new_research_without_clearing_original(self) -> None:
        halted = {"request": {"sequence": 9, "tool": self.module.AUTO}}
        self.queue.halted = halted
        for tool in self.module.READONLY_RESEARCH:
            with self.subTest(tool=tool):
                with self.assertRaises(RuntimeError):
                    asyncio.run(self.queue.call(
                        self.session,
                        {"sequence": 1, "tool": tool, "arguments": self.arguments(tool)},
                        Path("fixture-request.json"),
                    ))
        self.assertIs(self.queue.halted, halted)
        self.assertEqual(self.queue.next_sequence, 1)
        self.assertEqual(self.session.calls, [])

    def test_actual_call_keeps_one_existing_session_and_submits_only_two_reads(self) -> None:
        if RECEIPT_ROOT is None:
            raise RuntimeError("the bounded fixture needs an explicit receipt root")
        initial_save = self.queue.initial_save
        semantic = self.queue.semantic
        with tempfile.TemporaryDirectory(prefix="readonly-call-", dir=RECEIPT_ROOT) as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(RECEIPT_ROOT))
            queue_root = root / "sdk-session"
            outbox = root / "responses"
            queue_root.mkdir()
            outbox.mkdir()
            (root / "display-responses").mkdir()
            (root / "ROOT-ACTUAL-DRIVER-MODE.json").write_text(json.dumps({
                "episode_projection": "one_life", "before_submit_observation": True,
            }), encoding="utf-8")
            with mock.patch.multiple(self.module, N=root, Q=queue_root, OUTBOX=outbox), \
                    mock.patch.object(self.queue, "guard"):
                for sequence, tool in enumerate((self.module.DECLARABLE, self.module.NODE_IDENTITY), 1):
                    body, response = asyncio.run(self.queue.call(
                        self.session,
                        {"sequence": sequence, "tool": tool, "arguments": self.arguments(tool)},
                        root / f"fixture-request-{sequence}.json",
                    ))
                    self.assertEqual(body["status"], "available")
                    self.assertTrue(response.is_file())
                    retained = json.loads(response.read_text(encoding="utf-8"))
                    self.assertEqual(retained["request"]["tool"], tool)
                    self.assertNotIn("client_error", retained)
                self.assertEqual(len(list(queue_root.glob("INFLIGHT-*.json"))), 2)
        self.assertEqual(self.session.calls, [
            (self.module.DECLARABLE, self.arguments(self.module.DECLARABLE)),
            (self.module.NODE_IDENTITY, self.arguments(self.module.NODE_IDENTITY)),
        ])
        self.assertIs(self.queue.initial_save, initial_save)
        self.assertIs(self.queue.semantic, semantic)
        self.assertEqual(self.queue.frontend_done, 3)
        self.assertEqual(self.queue.loop_count, 0)
        self.assertEqual(self.queue.next_sequence, 3)
        self.assertIsNone(self.queue.halted)


def main() -> int:
    global QUEUE_HELPER_PATH, RECEIPT_ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue-helper", type=Path, required=True)
    parser.add_argument("--receipt-root", type=Path, required=True)
    parser.add_argument("--storage-admission", type=Path, required=True)
    parser.add_argument("--test", action="append", default=[])
    args = parser.parse_args()
    QUEUE_HELPER_PATH = args.queue_helper.resolve(strict=True)
    RECEIPT_ROOT = args.receipt_root.resolve()
    storage = _storage_check(args.storage_admission.resolve(strict=True), RECEIPT_ROOT)
    RECEIPT_ROOT.mkdir(parents=True, exist_ok=True)
    if any(RECEIPT_ROOT.iterdir()):
        raise RuntimeError("focused receipts require a new empty output directory")
    queue_sha = hashlib.sha256(QUEUE_HELPER_PATH.read_bytes()).hexdigest()
    stream = io.StringIO()
    suite = (
        unittest.TestSuite(FreshReadonlyResearchTests(name) for name in args.test)
        if args.test else
        unittest.defaultTestLoader.loadTestsFromTestCase(FreshReadonlyResearchTests)
    )
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    queue_unchanged = hashlib.sha256(QUEUE_HELPER_PATH.read_bytes()).hexdigest() == queue_sha
    receipt = {
        "status": "passed" if result.wasSuccessful() and queue_unchanged else "failed",
        "ended_at_utc": datetime.now(timezone.utc).isoformat(),
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "queue_helper": str(QUEUE_HELPER_PATH), "queue_helper_sha256": queue_sha,
        "queue_source_unchanged_during_run": queue_unchanged,
        "test_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "storage_start": storage,
        "actual_free_bytes_at_close": shutil.disk_usage(RECEIPT_ROOT).free,
        "open_kaishek_precheck": {"status": "not-applicable", "reason":
            "Python typed read-only route validation and fake MCP session; no CK3 script semantics"},
        "real_game_sdk_steam_window_activity": False,
    }
    log = stream.getvalue()
    encoded = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    if len(log.encode("utf-8")) + len(encoded.encode("utf-8")) > OUTPUT_LIMIT:
        raise RuntimeError("focused output exceeds its existing 1 MiB lane budget")
    (RECEIPT_ROOT / "unittest.log").write_text(log, encoding="utf-8")
    (RECEIPT_ROOT / "result.json").write_text(encoded, encoding="utf-8")
    print(log, end="")
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
