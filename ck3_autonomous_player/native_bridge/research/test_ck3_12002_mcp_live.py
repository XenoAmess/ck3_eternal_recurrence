"""Offline checks for MCP plan references and finite fixture inbox execution."""

from __future__ import annotations

import asyncio
from argparse import Namespace
from pathlib import Path
import tempfile
import threading
import time
import unittest

from run_ck3_12002_mcp_live import PlanClient, resolve, tool_payload


class OfflinePlanTests(unittest.TestCase):
    def test_native_fixture_invokes_only_fixed_step_and_restores_noop(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            client, report, source, inbox = self.inbox_case(root)
            calls = []

            async def invoke(name, arguments, **kwargs):
                calls.append((name, arguments))
                self.assertTrue(inbox.read_bytes().startswith(b"\xef\xbb\xbf"))
                self.assertIn("debug_log", inbox.read_text(encoding="utf-8-sig"))
                debug = client.args.state_dir / "profile/logs/debug.log"
                debug.parent.mkdir(parents=True)
                debug.write_text("XAR_FIXTURE: done\n", encoding="utf-8")
                return {"submission": {"command": "run xar_mcp_inbox.txt"}}

            client.invoke = invoke
            result = asyncio.run(client.write_inbox({
                "source_file": str(source), "debug_marker": "XAR_FIXTURE: done", "native_run": True,
            }))
            self.assertEqual(calls, [("ck3_migration_raw_step", {"step": "fixture-run-inbox-v1"})])
            self.assertTrue(result["native_invocation"]["ok"])
            self.assertTrue(result["marker_observed"])
            self.assertTrue(result["noop_restored"])
            self.assertNotIn("debug_log", inbox.read_text(encoding="utf-8-sig"))

    def test_partial_successful_turns_survive_next_tool_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = Namespace(output=Path(temporary) / "report.json", command_timeout=1)
            report = {"steps": []}
            client = PlanClient(None, args, report, lambda: None)
            calls = 0

            async def invoke(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 10:
                    raise RuntimeError("MCP tool error at turn ten")
                return {"status": "executed", "turn": calls}

            async def fresh():
                return {"revision": calls}

            client.invoke, client.fresh = invoke, fresh
            with self.assertRaisesRegex(RuntimeError, "turn ten"):
                asyncio.run(client.execute([{"id": "r2", "kind": "auto_turns", "count": 20}]))
            row = report["steps"][0]
            self.assertFalse(row["ok"])
            self.assertEqual(row["attempted_turns"], 10)
            self.assertEqual(row["completed_turns"], 9)
            self.assertEqual(len(row["result"]), 9)
            self.assertEqual(len(row["turn_snapshots"]), 9)

    def test_sdk_two_python_field_names_do_not_hide_tool_errors(self):
        from mcp import types
        success = types.CallToolResult(content=[], structured_content={"status": "executed"})
        self.assertEqual(tool_payload(success), {"status": "executed"})
        failure = types.CallToolResult(
            content=[types.TextContent(type="text", text="war-termination query unavailable")],
            is_error=True,
        )

        class ErrorSession:
            async def call_tool(self, *args, **kwargs):
                return failure

        with tempfile.TemporaryDirectory() as temporary:
            args = Namespace(output=Path(temporary) / "report.json", command_timeout=1)
            client = PlanClient(ErrorSession(), args, {}, lambda: None)
            with self.assertRaisesRegex(RuntimeError, "war-termination query unavailable"):
                asyncio.run(client.call("ck3_auto_turn"))

    def test_references_preserve_revision_army_ids_and_prior_query_identity(self):
        actual = resolve({
            "expected_revision": "$revision", "army_ids": "$army_ids",
            "character": {"$ref": "snapshot.played_character.character_id"},
            "token": "$results.query.candidate_token",
        }, {"revision": 7, "army_ids": [100, 200],
            "snapshot": {"played_character": {"character_id": 29829}},
            "results": {"query": {"candidate_token": "candidate-one"}}})
        self.assertEqual(actual, {"expected_revision": 7, "army_ids": [100, 200],
            "character": 29829, "token": "candidate-one"})

    def inbox_case(self, root: Path) -> tuple[PlanClient, dict[str, object], Path, Path]:
        args = Namespace(fixture_profile=True, state_dir=root / "candidate",
                         command_timeout=0.1, poll_interval=0.005, output=root / "report.json")
        source = root / "effect.txt"
        source.write_text('debug_log = "XAR_FIXTURE: done"\n', encoding="utf-8-sig")
        report: dict[str, object] = {}
        client = PlanClient(None, args, report, lambda: None)
        inbox = args.state_dir / "profile/run/xar_mcp_inbox.txt"
        return client, report, source, inbox

    def test_fixture_success_observes_new_marker_and_replaces_effect_with_noop(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            client, report, source, inbox = self.inbox_case(root)
            debug = client.args.state_dir / "profile/logs/debug.log"
            debug.parent.mkdir(parents=True)
            debug.write_text("old unrelated marker\n", encoding="utf-8")

            def observe_fixture() -> None:
                deadline = time.monotonic() + 1
                while not inbox.exists() and time.monotonic() < deadline:
                    time.sleep(0.002)
                with debug.open("a", encoding="utf-8") as stream:
                    stream.write("XAR_FIXTURE: done\n")
            thread = threading.Thread(target=observe_fixture)
            thread.start()
            try:
                result = asyncio.run(client.write_inbox({
                    "source_file": str(source), "debug_marker": "XAR_FIXTURE: done", "timeout": 1,
                }))
            finally:
                thread.join()
            self.assertTrue(result["marker_observed"])
            self.assertTrue(result["noop_restored"])
            self.assertTrue(inbox.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertNotIn("debug_log", inbox.read_text(encoding="utf-8-sig"))

    def test_fixture_timeout_also_stops_repeated_effect_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            client, report, source, inbox = self.inbox_case(root)
            with self.assertRaises(TimeoutError):
                asyncio.run(client.write_inbox({
                    "source_file": str(source), "debug_marker": "XAR_FIXTURE: missing", "timeout": 0.015,
                }))
            self.assertTrue(report["fixture_inbox_attempts"][0]["noop_restored"])
            self.assertNotIn("debug_log", inbox.read_text(encoding="utf-8-sig"))


if __name__ == "__main__":
    unittest.main()
