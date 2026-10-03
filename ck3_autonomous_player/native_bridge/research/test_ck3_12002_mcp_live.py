"""Offline checks for MCP plan references and finite fixture inbox execution."""

from __future__ import annotations

import asyncio
from argparse import Namespace
from contextlib import nullcontext
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest import mock

from run_ck3_12002_mcp_live import (
    PlanClient, clean_imports, fixture_session,
    require_verified_bookmarks_picker, resolve, tool_payload,
)


class OfflinePlanTests(unittest.TestCase):
    def test_unknown_or_incomplete_tree_never_admits_direct_bookmarks(self):
        # Unit fixtures exercise admission only; real runs must obtain native
        # tree/model observations before selecting or starting a character.
        base = {"schema": "ck3-frontend-gui-tree-inspection-v1", "accepted": True,
                "status": "available", "scope_root_name": "frontend_bookmarks",
                "root_available": True, "read_only": True, "truncated": False,
                "widgets": [{"runtime_name": name, "child_path": "" if index == 0 else str(index),
                             "vtable_rva": 1, "effective_visible": True, "enabled": True}
                            for index, name in enumerate(["frontend_bookmarks", "character_selection",
                                                         "start_button", "pick_any_character_button"])]}
        self.assertEqual(require_verified_bookmarks_picker(base)["status"], "ORDINARY_BOOKMARKS_TREE_VERIFIED")
        bad = [dict(base, truncated=True), dict(base, scope_root_name="mainmenu_panel_bottom"),
               dict(base, widgets=[r for r in base["widgets"] if r["runtime_name"] != "start_button"]),
               dict(base, widgets=base["widgets"]+[base["widgets"][2]])]
        for tree in bad:
            with self.subTest(tree=tree):
                with self.assertRaises(RuntimeError): require_verified_bookmarks_picker(tree)

    def test_fixture_session_consumes_next_episode_queue_and_relaunches(self):
        clean_imports(Path(__file__).resolve().parents[2] / "src")
        session_module = importlib.import_module("xar_autoplayer.native_session")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = Namespace(state_dir=root / "state", profile_dir=root / "state/profile",
                             game_exe=root / "ck3.exe")
            config = Namespace(mode="native-headless", pipe_name=r"\\.\pipe\fixture-session-test")
            args = Namespace(timeout=1, hold_seconds=0, cold_start_checkpoint=False)
            seed = spec.profile_dir / "save games/xar_episode_seed.ck3"
            seed.parent.mkdir(parents=True)
            seed.write_bytes(b"immutable fixture seed")
            digest = hashlib.sha256(seed.read_bytes()).hexdigest()
            bridge = spec.state_dir / "native-session/bridge"
            inbox = bridge / "inbox"
            inbox.mkdir(parents=True)
            (inbox / "01-next.json").write_text(json.dumps({
                "protocol_version": 1, "request_id": "01-next", "command": "start-next-episode",
                "pipe": config.pipe_name, "seed_name": seed.name, "seed_size": seed.stat().st_size,
                "seed_sha256": digest, "seed_date_raw": 53168784,
                "seed_character_id": 29829, "source_run_id": "fixture-death-complete",
            }), encoding="utf-8")
            (inbox / "02-stop.json").write_text(json.dumps({
                "protocol_version": 1, "request_id": "02-stop", "command": "stop",
            }), encoding="utf-8")
            first = Namespace(process=mock.Mock(pid=4545))
            second = Namespace(process=mock.Mock(pid=4646))
            first.process.poll.return_value = second.process.poll.return_value = None
            stream = io.StringIO()
            with mock.patch.object(session_module, "launch", side_effect=(first, second)) as launch, \
                    mock.patch.object(session_module, "stop_tracked", return_value={"ok": True}) as stop, \
                    mock.patch.object(session_module, "_process_windows_minimized", return_value=False), \
                    mock.patch.object(session_module, "validate_native_bridge_launch_config", return_value=config), \
                    mock.patch.object(session_module, "ensure_state_path_safe"), \
                    mock.patch.object(session_module, "exclusive_launch_lock", return_value=nullcontext()), \
                    mock.patch.object(session_module, "exclusive_state_lock", return_value=nullcontext()):
                report = fixture_session(spec, config, args, threading.Event(), output_stream=stream)
                self.assertIs(session_module.launch, launch)
            self.assertEqual(launch.call_args_list, [
                mock.call(spec, native_bridge=config, continue_last_save=True, verify_prepared_profile=False),
                mock.call(spec, native_bridge=config, load_save_name="xar_episode_seed", verify_prepared_profile=False),
            ])
            self.assertEqual(stop.call_args_list, [
                mock.call(first, require_running=False), mock.call(second, require_running=False),
            ])
            response = json.loads((bridge / "outbox/01-next.json").read_text(encoding="utf-8"))
            self.assertTrue(response["ok"])
            self.assertEqual(response["result"]["lifecycle_intent"], "new_episode")
            self.assertEqual(response["result"]["episode_seed"]["sha256"], digest)
            self.assertEqual(report["restart_count"], 1)
            self.assertEqual(report["exit_reason"], "stop")
            self.assertTrue(report["ok"])
            self.assertTrue(report["fixture_profile"])
            self.assertIn('"type": "native_session_episode_started"', stream.getvalue())

    def test_unpaused_active_event_interrupts_advance_and_keeps_followup_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = Namespace(output=Path(temporary) / "report.json", command_timeout=180,
                             poll_interval=3600)
            report = {"steps": []}
            client = PlanClient(None, args, report, lambda: None)
            event = {"event_instance_id": 14, "enabled_option_count": 2}
            state = {"paused": True, "speed": 1, "date_raw": 53168784, "active_event": None}
            calls = []
            snapshots = []

            async def invoke(name, arguments=None, **kwargs):
                if name == "ck3_execute_step":
                    calls.append(arguments["step"])
                    if arguments["step"] == "resume-map":
                        state.update(paused=False, date_raw=53169024, active_event=event)
                    elif arguments["step"] == "pause-map":
                        state["paused"] = True
                    return {"status": "executed"}
                calls.append(name)
                return event

            async def fresh():
                snapshots.append(dict(state))
                return dict(state)

            client.invoke, client.fresh = invoke, fresh
            asyncio.run(asyncio.wait_for(client.execute([
                {"id": "advance", "kind": "advance_day", "days": 17, "timeout": 180,
                 "continue_on_error": True},
                {"id": "event", "tool": "query-event"},
            ]), timeout=0.2))
            self.assertEqual(calls, ["pause-map", "set-speed-1", "resume-map", "pause-map", "query-event"])
            self.assertTrue(state["paused"])
            self.assertFalse(snapshots[2]["paused"])
            self.assertEqual(snapshots[2]["active_event"], event)
            interrupted, followup = report["steps"]
            self.assertFalse(interrupted["ok"])
            self.assertIn("date_raw=53169024", interrupted["error"])
            self.assertIn("paused=False", interrupted["error"])
            self.assertIn('"event_instance_id": 14', interrupted["error"])
            self.assertTrue(followup["ok"])
            self.assertEqual(followup["result"], event)

    def test_nested_hold_finishes_first_control_plan_before_next_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controls = root / "controls"
            controls.mkdir()
            (controls / "001.json").write_text(json.dumps({"steps": [
                {"id": "submit1", "tool": "submit1"},
                {"id": "settle", "kind": "hold", "seconds": 0.002},
                {"id": "settled", "tool": "nestedholdend"},
            ]}), encoding="utf-8-sig")
            (controls / "002.json").write_text(json.dumps({"steps": [
                {"id": "submit2", "tool": "submit2"},
            ]}), encoding="utf-8-sig")
            args = Namespace(output=root / "report.json", command_timeout=1,
                             control_plan_dir=controls, hold_seconds=0)
            report = {"steps": []}
            client = PlanClient(None, args, report, lambda: None)
            calls = []

            async def invoke(name, arguments, **kwargs):
                calls.append(name)
                return {"submitted": True}

            async def fresh():
                return {"revision": len(calls)}

            client.invoke, client.fresh = invoke, fresh
            asyncio.run(client.hold(0.01))
            self.assertEqual(calls, ["submit1", "nestedholdend", "submit2"])
            self.assertEqual(client.control_plan_execution_depth, 0)
            asyncio.run(client.hold(0.002))
            self.assertEqual(calls, ["submit1", "nestedholdend", "submit2"])
            self.assertEqual(len(client.consumed_control_plans), 2)

    def test_nested_hold_consumes_each_control_file_identity_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controls = root / "controls"
            controls.mkdir()
            control = controls / "001.json"
            control.write_text(json.dumps({"steps": [
                {"id": "submit", "tool": "fixture-submit"},
                {"id": "settle", "kind": "hold", "seconds": 0.002},
            ]}), encoding="utf-8-sig")
            args = Namespace(output=root / "report.json", command_timeout=1,
                             control_plan_dir=controls, hold_seconds=0)
            report = {"steps": []}
            client = PlanClient(None, args, report, lambda: None)
            calls = []

            async def invoke(name, arguments, **kwargs):
                calls.append(name)
                return {"submitted": True}

            async def fresh():
                return {"revision": len(calls)}

            client.invoke, client.fresh = invoke, fresh
            asyncio.run(client.hold(0.01))
            self.assertEqual(calls, ["fixture-submit"])
            asyncio.run(client.hold(0.002))
            self.assertEqual(calls, ["fixture-submit"])
            old = control.stat()
            os.utime(control, ns=(old.st_atime_ns, old.st_mtime_ns + 1_000_000))
            asyncio.run(client.hold(0.01))
            self.assertEqual(calls, ["fixture-submit", "fixture-submit"])
            asyncio.run(client.hold(0.002))
            self.assertEqual(calls, ["fixture-submit", "fixture-submit"])
            self.assertEqual(len(client.consumed_control_plans), 2)
            self.assertEqual(len(report["control_plans"]), 2)

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
