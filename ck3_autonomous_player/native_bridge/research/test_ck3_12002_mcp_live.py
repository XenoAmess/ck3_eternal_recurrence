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
    def test_explicit_rules_diagnostic_new_game_is_once_and_default_dispatches_nothing(self):
        import run_ck3_12002_mcp_live as harness
        route = {"schema": "ck3-frontend-gui-route-v1", "accepted": True, "route": "main_menu"}
        tree = {"schema": "ck3-frontend-gui-tree-inspection-v1", "accepted": True,
                "status": "available", "scope_root_name": "mainmenu_panel_bottom",
                "root_available": True, "read_only": True, "truncated": False,
                "widget_count": 2, "widgets": [
                    {"runtime_name": "mainmenu_panel_bottom", "child_path": "", "vtable_rva": 1,
                     "effective_visible": True, "enabled": True},
                    {"runtime_name": "new_game_button", "child_path": "1", "vtable_rva": 2,
                     "effective_visible": True, "enabled": True}]}
        proof = {"consecutive_consistent_observations": 2}
        bookmarks = dict(route, route="bookmarks")
        bookmark_tree = dict(tree, scope_root_name="frontend_bookmarks", widgets=[
            dict(tree["widgets"][0], runtime_name="frontend_bookmarks"),
            dict(tree["widgets"][1], runtime_name="game_rules_button")])
        class Client:
            def __init__(self, fail=False):
                self.calls = []
                self.fail = fail
                self.packets = iter([bookmarks, bookmark_tree, bookmarks] * 2)
            async def call(self, name):
                self.calls.append(name)
                if name == "ck3_activate_frontend_new_game_v1":
                    if self.fail:
                        raise RuntimeError("callback result lost after request")
                    return {"status": "verified"}
                return next(self.packets)
        def invoke(client, report, allowed):
            return asyncio.run(harness.prepare_rules_diagnostic_bookmarks(
                client, route=route, tree=tree, proof=proof, allow_new_game=allowed,
                report=report, write=lambda: None, timeout=1))
        default = Client()
        with self.assertRaises(RuntimeError):
            invoke(default, {"frontend_bootstrap": {"attempts": []}}, False)
        self.assertEqual(default.calls, [])
        client = Client()
        report = {"frontend_bootstrap": {"attempts": []}}
        result = invoke(client, report, True)
        self.assertEqual(result[0]["route"], "bookmarks")
        self.assertEqual(result[2]["consecutive_consistent_observations"], 2)
        self.assertEqual(client.calls.count("ck3_activate_frontend_new_game_v1"), 1)
        self.assertTrue(all(name in {"ck3_activate_frontend_new_game_v1", "ck3_query_frontend_gui_route_v1",
                                    "ck3_inspect_frontend_gui_tree_v1"} for name in client.calls))
        self.assertFalse(report["frontend_bootstrap"]["diagnostic_new_game_request"]["retry_allowed"])
        self.assertEqual(len(report["frontend_bootstrap"]["attempts"]), 2)
        failed = Client(fail=True)
        failed_report = {"frontend_bootstrap": {"attempts": []}}
        with self.assertRaises(RuntimeError):
            invoke(failed, failed_report, True)
        with self.assertRaises(RuntimeError):
            invoke(failed, failed_report, True)
        self.assertEqual(failed.calls, ["ck3_activate_frontend_new_game_v1"])
        self.assertIn("diagnostic_new_game_request", failed_report["frontend_bootstrap"])
        parsed = harness.parser().parse_args([])
        self.assertFalse(parsed.frontend_rules_diagnostic_new_game)

    def test_frontend_readiness_rejects_transient_route_tree_and_resets_streak(self):
        import run_ck3_12002_mcp_live as harness
        from copy import deepcopy
        route = {"schema": "ck3-frontend-gui-route-v1", "accepted": True, "route": "bookmarks"}
        unavailable = dict(route, route="unavailable")
        tree = {"schema": "ck3-frontend-gui-tree-inspection-v1", "accepted": True,
                "status": "available", "scope_root_name": "frontend_bookmarks",
                "root_available": True, "read_only": True, "truncated": False,
                "widget_count": 2, "widgets": [
                    {"runtime_name": "frontend_bookmarks", "child_path": "", "vtable_rva": 1,
                     "effective_visible": True, "enabled": True},
                    {"runtime_name": "game_rules_button", "child_path": "1", "vtable_rva": 2,
                     "effective_visible": True, "enabled": True}]}
        # The actual R0003 packet was route=bookmarks, tree=_root_ truncated,
        # followed by unavailable. It must never admit a rules opener.
        transient = dict(tree, scope_root_name="_root_", truncated=True)
        with self.assertRaises(RuntimeError):
            harness.require_consistent_frontend_observation(route, transient, unavailable, require_rules_button=True)
        invisible = deepcopy(tree)
        invisible["widgets"][0]["effective_visible"] = False
        with self.assertRaises(RuntimeError):
            harness.require_consistent_frontend_observation(route, invisible, route, require_rules_button=True)
        packets = iter([route, transient, unavailable, route, tree, route,
                        unavailable, route, tree, route, route, tree, route])
        calls = []
        class Client:
            async def call(self, name):
                calls.append(name)
                return next(packets)
        report = {"frontend_bootstrap": {"attempts": []}}
        result = asyncio.run(harness.wait_for_consistent_frontend(
            Client(), report=report, write=lambda: None, timeout=1,
            require_route="bookmarks", require_rules_button=True, poll_interval=0))
        self.assertEqual(result[2]["consecutive_consistent_observations"], 2)
        attempts = report["frontend_bootstrap"]["attempts"]
        self.assertEqual([row.get("consecutive_consistent_observations", 0) for row in attempts], [0, 1, 0, 1, 2])
        self.assertEqual(attempts[0]["tree"]["scope_root_name"], "_root_")
        self.assertTrue(attempts[0]["tree"]["truncated"])
        self.assertTrue(all(name in {"ck3_query_frontend_gui_route_v1", "ck3_inspect_frontend_gui_tree_v1"} for name in calls))

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

    def test_campaign_d1_actor_transition_wait_is_explicit_before_terminal_pause(self):
        # R9 thin states: D1 date publishes with old actor before the new native
        # actor frame. Only the mocked command ACK and pause postcondition vary.
        before = {"date_raw": 53144328, "paused": True, "speed": 1,
            "active_event": None, "map_ready": True, "native_revision": 4,
            "episode_projection": "native_campaign", "local_player_id": 1,
            "played_character": {"character_id": 34422, "alive": True, "source": "native"},
            "diagnostics": {"bridge_pid": 16256, "connection_generation": 1,
                "pipe_name": "actual-R9-bound-pipe", "last_heartbeat": {
                    "snapshot_observer_12002": {"started_ms": 567866593,
                        "completed_ms": 567866593, "read_in_progress": False}}}}
        for opted_in in (False, True):
            with self.subTest(opted_in=opted_in), tempfile.TemporaryDirectory() as temporary:
                client = PlanClient(None, Namespace(output=Path(temporary) / "report.json",
                    command_timeout=180, poll_interval=0), {"steps": []}, lambda: None)
                old_actor = json.loads(json.dumps(before))
                old_actor.update(date_raw=53144352, paused=False, native_revision=8)
                new_actor = json.loads(json.dumps(old_actor))
                new_actor["played_character"]["character_id"] = 29959
                new_actor["native_revision"] = 9
                trajectory = [old_actor, new_actor]
                control = {"stage": "before", "index": 0}
                calls, observed = [], []

                async def fresh():
                    if control["stage"] == "before":
                        value = before
                    elif control["stage"] == "paused":
                        value = dict(client.snapshot, paused=True)
                    else:
                        value = trajectory[control["index"]]
                        control["index"] += 1
                    client.snapshot = json.loads(json.dumps(value))
                    observed.append(client.snapshot["played_character"]["character_id"])
                    return client.snapshot

                async def invoke(name, arguments=None, **kwargs):
                    self.assertEqual(name, "ck3_execute_step")
                    step = arguments["step"]
                    calls.append(step)
                    if step == "resume-map":
                        control["stage"] = "running"
                    elif step == "pause-map" and control["stage"] == "running":
                        self.assertEqual(observed[-1], 29959 if opted_in else 34422)
                        control["stage"] = "paused"
                    return {"accepted": True, "status": "submitted"}

                client.fresh, client.invoke = fresh, invoke
                row = {"days": 1}
                if opted_in:
                    row["wait_for_played_character_change"] = True
                result = asyncio.run(client.advance(row))
                self.assertEqual(calls, ["pause-map", "set-speed-1", "resume-map", "pause-map"])
                self.assertEqual(control["index"], 2 if opted_in else 1)
                self.assertEqual(result["elapsed_hours"], 24)
                self.assertTrue(result["after"]["paused"])

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



class RuntimeEpisodeIdentityTests(unittest.TestCase):
    def client_case(self, directory, character=31254, *, campaign_mismatch=False, event_mismatch=False, stale_query=False):
        import copy
        args = Namespace(output=Path(directory) / "report.json", command_timeout=1)
        report, calls = {"steps": []}, []
        client = PlanClient(None, args, report, lambda: None)
        state = {"map_ready": True, "paused": True, "backend_id": "native-headless",
                 "source": "injected-dll-named-pipe", "played_character":
                 {"character_id": character, "alive": True, "source": "native"},
                 "episode_character_id": character, "episode_run_id": "episode-original",
                 "one_life_terminal": False, "revision": 47, "native_revision": 17,
                 "snapshot_id": "native:17", "date_raw": 53144328, "local_player_id": 1,
                 "active_event": {"instance_id": 1073741859}, "diagnostics":
                 {"bridge_pid": 17001, "connection_generation": 3, "hello":
                  {"expected_ck3_version": "1.20.0.3", "expected_ck3_sha256": "CURRENT-EXACT-SHA"}}}
        query_revision = 47
        async def call(name, arguments=None):
            calls.append((name, copy.deepcopy(arguments)))
            if name == "ck3_take_snapshot":
                return copy.deepcopy(state)
            if name == "ck3_query_campaign_root_context_v1":
                self.assertEqual(arguments, {"expected_revision": 47})
                return {"status": "available", "campaign_root_context_ready": True,
                        "binding": {"snapshot_id": "native:17", "revision": 47,
                                    "native_revision": 17, "date_raw": 53144328, "expected_revision": 47},
                        "build": {"version": "1.20.0.3", "exe_sha256": "CURRENT-EXACT-SHA"},
                        "campaign_root_context": {"player_character_id": character + 1 if campaign_mismatch else character,
                                                  "player_character_alive": True, "local_player_id": 1,
                                                  "snapshot_revision": 17, "date_raw": 53144328}}
            if name == "ck3_query_current_event_window_context_v1":
                self.assertEqual(arguments, {"event_instance_id": 1073741859, "expected_revision": query_revision})
                return {"queried_revision": query_revision + int(stale_query),
                        "current_event_window_context": {"current_event_instance_id": 1073741859,
                            "event_definition_key": "cca120.12", "root_scope": {"type_key": "character",
                            "typed_identity": {"status": "available", "kind": "character",
                                               "character_id": character + 1 if event_mismatch else character}}}}
            if name == "ck3_select_event_option":
                self.assertEqual(arguments, {"option_number": 1, "event_instance_id": 1073741859,
                                             "expected_revision": query_revision})
                state.update(one_life_terminal=True, revision=48, native_revision=18, snapshot_id="native:18")
                state["played_character"] = {"character_id": 88001, "alive": True, "source": "native"}
                raise RuntimeError("callback result unavailable after actual death submission")
            if name == "ck3_settle_one_life":
                return {"episode_character_id": character, "one_life_settlement": {"source_character_id": character}}
            if name == "literal":
                return {"name": "$legacy", "object": {"value": "$legacy"}}
            raise AssertionError("Unexpected tool " + name)
        client.call = call
        client.tools = {"ck3_query_campaign_root_context_v1": {"inputSchema": {"properties": {"expected_revision": {}}}},
                        "ck3_query_current_event_window_context_v1": {"inputSchema": {"properties": {"expected_revision": {}}}},
                        "ck3_select_event_option": {"inputSchema": {"properties": {"expected_revision": {}}}}}
        return client, report, calls, state

    def event_steps(self):
        return [
            {"id": "frame", "tool": "ck3_take_snapshot", "expect": {
                "played_character.character_id": {"$ref": "episode.runtime_character_id"},
                "episode_character_id": {"$ref": "episode.episode_character_id"},
                "diagnostics.bridge_pid": {"$ref": "episode.bridge_pid"},
                "diagnostics.connection_generation": {"$ref": "episode.connection_generation"}}},
            {"id": "event-query", "tool": "ck3_query_current_event_window_context_v1", "args": {
                "event_instance_id": "$results.frame.active_event.instance_id", "expected_revision": "$results.frame.revision"},
             "expect": {"current_event_window_context.event_definition_key": "cca120.12",
                        "current_event_window_context.root_scope.typed_identity.character_id": {"$ref": "episode.runtime_character_id"},
                        "current_event_window_context.current_event_instance_id": {"$ref": "results.frame.active_event.instance_id"},
                        "queried_revision": {"$ref": "results.frame.revision"}}},
            {"id": "death-once", "tool": "ck3_select_event_option", "continue_on_error": True,
             "args": {"option_number": 1, "event_instance_id": "$results.event-query.current_event_window_context.current_event_instance_id",
                      "expected_revision": "$results.event-query.queried_revision"}},
            {"id": "terminal", "tool": "ck3_take_snapshot", "expect": {"one_life_terminal": True,
                "episode_character_id": {"$ref": "episode.episode_character_id"}}},
            {"id": "settle", "tool": "ck3_settle_one_life", "expect": {
                "episode_character_id": {"$ref": "episode.episode_character_id"},
                "one_life_settlement.source_character_id": {"$ref": "episode.runtime_character_id"}}}]

    def test_dynamic_episode_keeps_original_settlement_source_after_heir_change(self):
        for character in (31254, 78651):
            with self.subTest(character=character), tempfile.TemporaryDirectory() as temporary:
                client, report, calls, state = self.client_case(temporary, character)
                asyncio.run(client.execute([{"id": "anchor", "kind": "episode_identity_anchor", "expect": {"verified": True}}]))
                report["steps"][0]["result"]["runtime_character_id"] = 99999
                self.assertEqual(client.episode_identity["runtime_character_id"], character)
                asyncio.run(client.execute(self.event_steps()))
                self.assertEqual(sum(name == "ck3_select_event_option" for name, _ in calls), 1)
                self.assertEqual(state["played_character"]["character_id"], 88001)
                self.assertEqual(client.episode_identity["runtime_character_id"], character)
                self.assertFalse(report["steps"][3]["ok"])
                self.assertTrue(report["steps"][-1]["ok"])
                self.assertEqual(report["steps"][-1]["resolved_expect"]["one_life_settlement.source_character_id"], character)
                with self.assertRaisesRegex(ValueError, "already anchored"):
                    asyncio.run(client.bind_episode_identity())

    def test_wrong_campaign_or_event_root_and_stale_revision_prevent_death_submission(self):
        for mode in ("campaign_mismatch", "event_mismatch", "stale_query"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                client, report, calls, _ = self.client_case(temporary, **{mode: True})
                with self.assertRaises(ValueError):
                    asyncio.run(client.execute([{"id": "anchor", "kind": "episode_identity_anchor"}] + self.event_steps()))
                self.assertFalse(any(name == "ck3_select_event_option" for name, _ in calls))
                self.assertFalse(report["steps"][-1]["ok"])

    def test_anchor_rejects_boolean_zero_missing_identity_and_pid_generation_changes(self):
        for invalid in (True, 0, None):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as temporary:
                client, _, calls, state = self.client_case(temporary)
                state["played_character"]["character_id"] = invalid
                state["episode_character_id"] = invalid
                with self.assertRaises(ValueError):
                    asyncio.run(client.bind_episode_identity())
                self.assertFalse(any(name == "ck3_query_campaign_root_context_v1" for name, _ in calls))
        for changed in ("bridge_pid", "connection_generation"):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as temporary:
                client, _, calls, state = self.client_case(temporary)
                original = client.call
                async def crossed(name, arguments=None):
                    result = await original(name, arguments)
                    if name == "ck3_query_campaign_root_context_v1":
                        state["diagnostics"][changed] += 1
                    return result
                client.call = crossed
                with self.assertRaisesRegex(ValueError, "frame changed"):
                    asyncio.run(client.bind_episode_identity())
                self.assertIsNone(client.episode_identity)

    def test_only_explicit_expect_refs_resolve_and_missing_anchor_blocks_followup(self):
        with tempfile.TemporaryDirectory() as temporary:
            client, report, calls, _ = self.client_case(temporary)
            asyncio.run(client.execute([{"id": "literal", "tool": "literal", "expect": {
                "name": "$legacy", "object": {"value": "$legacy"}}}]))
            self.assertTrue(report["steps"][0]["ok"])
            with self.assertRaises(TypeError):
                asyncio.run(client.execute(self.event_steps()))
            self.assertFalse(any(name == "ck3_select_event_option" for name, _ in calls))

class WriterEventBoundaryTests(unittest.TestCase):
    def client_case(self, temporary, *, offset=1, event=True, pause_event=False, owner_change=None, instance_change=False, speed_event=False, speed_owner=None):
        from copy import deepcopy
        client = PlanClient(None, Namespace(output=Path(temporary) / "report.json", command_timeout=1,
                                            poll_interval=0), {"steps": []}, lambda: None)
        state = {"map_ready": True, "paused": True, "speed": 1, "active_event": None,
                 "played_character": {"character_id": 31254, "alive": True, "source": "native"},
                 "episode_character_id": 31254, "episode_run_id": "actual-episode",
                 "one_life_terminal": False, "backend_id": "native-headless", "source": "injected-dll-named-pipe",
                 "snapshot_id": "native:7", "revision": 8, "native_revision": 7, "date_raw": 53144328,
                 "local_player_id": 1, "diagnostics": {"bridge_pid": 1208, "connection_generation": 1}}
        client.episode_identity = {"runtime_character_id": 31254, "episode_run_id": "actual-episode",
                                   "bridge_pid": 1208, "connection_generation": 1}
        capabilities = {"snapshot": True, "action_steps": ["pause-map", "resume-map", "set-speed-1"],
                        "bridge_capabilities": ["game.command.query-current-event-window-context-v1"],
                        "current_event_window_context_v1_query_supported": True}
        calls, running = [], False
        async def call(name, arguments=None):
            nonlocal running
            calls.append((name, deepcopy(arguments)))
            if name == "ck3_get_capabilities":
                return deepcopy(capabilities)
            if name == "ck3_take_snapshot":
                if running and not state["paused"]:
                    state["date_raw"] = 53144328 + offset
                    if event:
                        state["active_event"] = {"instance_id": 1073741859, "event_id": "raw-observation"}
                return deepcopy(state)
            if name == "ck3_execute_step":
                primitive = arguments["step"]
                if primitive == "resume-map":
                    running, state["paused"] = True, False
                elif primitive == "pause-map":
                    state["paused"] = True
                    if running and pause_event:
                        state["active_event"] = {"instance_id": 1073741859, "event_id": "raw-observation"}
                    if running and owner_change:
                        state["diagnostics"][owner_change] += 1
                    if running and instance_change:
                        state["active_event"]["instance_id"] += 1
                elif primitive == "set-speed-1":
                    state["speed"] = 1
                    if speed_event:
                        state["active_event"] = {"instance_id": 1073741859, "event_id": "during-speed"}
                    if speed_owner:
                        state["diagnostics"][speed_owner] += 1
                else:
                    raise AssertionError("Unsupported primitive " + primitive)
                return {"step": primitive, "accepted": True}
            raise AssertionError("Unexpected tool " + name)
        client.call = call
        client.tools = {name: {"inputSchema": {"properties": {}}} for name in
                        ("ck3_get_capabilities", "ck3_take_snapshot", "ck3_execute_step",
                         "ck3_query_current_event_window_context_v1")}
        return client, capabilities, calls

    def test_actual_r7_no_event_capability_projection_admits_time_and_rejects_missing_observer(self):
        # Sanitized actual paused/no-event R7 response at 2026-10-03T18:06:33.914833Z.
        # Capture SHA256 de3c569146c3b1bb39c6926c92e979460370d5fc3cd052eb794296dad927ca76.
        # Keep the actual action list; only unrelated HELLO capabilities are omitted.
        actual_no_event = (
        {'action_steps': ['activate-frontend-game-rules-v1',
                          'activate-frontend-new-game-v1',
                          'activate-frontend-select-supported-1066-character-v1',
                          'activate-frontend-start-selected-bookmark-v1',
                          'apply-and-hide-frontend-game-rules-v1',
                          'hide-frontend-game-rules-v1',
                          'inspect-frontend-gui-tree-v1',
                          'inspect-gui-window-tree-v1',
                          'life-advance',
                          'pause-map',
                          'probe-frontend-bookmark-model-v1',
                          'query-army-strengths-v1',
                          'query-arrange-marriage-choices',
                          'query-campaign-root-context-v1',
                          'query-declarable-wars',
                          'query-frontend-applied-game-rules-v1',
                          'query-frontend-game-rule-selections-v1',
                          'query-frontend-game-rules-window-v1',
                          'query-frontend-gui-route-v1',
                          'query-loaded-feature-manifest-v1',
                          'query-steward-develop-county-candidates-v1',
                          'resume-map',
                          'save-checkpoint',
                          'select-frontend-game-rule-v1',
                          'set-speed-1',
                          'set-speed-2',
                          'set-speed-3',
                          'set-speed-4',
                          'set-speed-5'],
         'bridge_capabilities': ['game.command.query-current-event-window-context-v1'],
         'current_event_window_context_v1_query_supported': True,
         'snapshot': True}
        )
        self.assertNotIn("query-current-event-window-context-v1", actual_no_event["action_steps"])
        with tempfile.TemporaryDirectory() as temporary:
            client, caps, calls = self.client_case(temporary)
            caps.clear()
            caps.update(actual_no_event)
            result = asyncio.run(client.advance_event_boundary({"days": 1, "allow_event_boundary": True}))
            self.assertEqual(result["progress_status"], "event_before_target")
            self.assertFalse(result["requested_interval_complete"])
            self.assertEqual(sum(name == "ck3_execute_step" and args["step"] == "resume-map" for name, args in calls), 1)
        for missing in ("backend-observer-capability", "registered-observer-tool"):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as temporary:
                client, caps, calls = self.client_case(temporary)
                caps.clear()
                caps.update(actual_no_event)
                if missing == "backend-observer-capability":
                    caps["bridge_capabilities"] = []
                else:
                    client.tools.pop("ck3_query_current_event_window_context_v1")
                with self.assertRaises(ValueError):
                    asyncio.run(client.advance_event_boundary({"days": 1, "allow_event_boundary": True}))
                self.assertFalse(any(name == "ck3_execute_step" for name, _ in calls))

    def test_capability_and_explicit_boundary_contract_reject_before_game_mutation(self):
        for missing in ("pause-map", "resume-map", "set-speed-1", "observer-capability", "typed-query", "opt-in"):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as temporary:
                client, caps, calls = self.client_case(temporary)
                step = {"days": 1, "allow_event_boundary": True}
                if missing == "typed-query":
                    caps["current_event_window_context_v1_query_supported"] = False
                elif missing == "observer-capability":
                    caps["bridge_capabilities"] = []
                elif missing == "opt-in":
                    step.pop("allow_event_boundary")
                else:
                    caps["action_steps"].remove(missing)
                with self.assertRaises(ValueError):
                    asyncio.run(client.advance_event_boundary(step))
                self.assertFalse(any(name == "ck3_execute_step" for name, _ in calls))

    def test_event_observation_retains_early_progress_and_default_advance_dispatch(self):
        for offset, event, pause_event, complete, status in ((1, True, False, False, "event_before_target"),
                                                            (24, True, False, True, "event_at_target"),
                                                            (24, False, True, True, "event_at_target"),
                                                            (24, False, False, True, "target_date_reached")):
            with self.subTest(offset=offset, event=event, pause_event=pause_event), tempfile.TemporaryDirectory() as temporary:
                client, _, calls = self.client_case(temporary, offset=offset, event=event, pause_event=pause_event)
                result = asyncio.run(client.advance_event_boundary({"days": 1, "allow_event_boundary": True}))
                self.assertEqual(result["requested_interval_complete"], complete)
                self.assertEqual(result["progress_status"], status)
                self.assertTrue(result["after"]["paused"])
                self.assertEqual(result["selected_event_options"], 0)
                self.assertEqual([args["step"] for name, args in calls if name == "ck3_execute_step"],
                                 ["pause-map", "set-speed-1", "resume-map", "pause-map"])
                if event or pause_event:
                    self.assertEqual(result["event_boundary"]["active_event"]["instance_id"], 1073741859)
                    self.assertEqual(result["event_resolution"], "typed_query_required")
        with tempfile.TemporaryDirectory() as temporary:
            client, _, _ = self.client_case(temporary)
            client.advance = mock.AsyncMock(return_value={"legacy": True})
            client.advance_event_boundary = mock.AsyncMock(side_effect=AssertionError("Unrequested opt-in"))
            asyncio.run(client.execute([{"id": "legacy", "kind": "advance_day", "days": 17}]))
            client.advance.assert_awaited_once()
            client.advance_event_boundary.assert_not_called()

    def test_speed_readback_event_or_owner_change_prevents_any_resume(self):
        for mode in ("event", "bridge_pid", "connection_generation"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                client, _, calls = self.client_case(temporary, speed_event=mode == "event",
                                                    speed_owner=mode if mode != "event" else None)
                with self.assertRaises(ValueError):
                    asyncio.run(client.advance_event_boundary({"days": 1, "allow_event_boundary": True}))
                self.assertEqual([args["step"] for name, args in calls if name == "ck3_execute_step"],
                                 ["pause-map", "set-speed-1"])

    def test_paused_boundary_rejects_owner_or_full_instance_change(self):
        for mode in ("bridge_pid", "connection_generation", "instance"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                client, _, calls = self.client_case(temporary, owner_change=mode if mode != "instance" else None,
                                                    instance_change=mode == "instance")
                with self.assertRaises(ValueError):
                    asyncio.run(client.advance_event_boundary({"days": 1, "allow_event_boundary": True}))
                self.assertEqual(sum(name == "ck3_execute_step" and args["step"] == "resume-map" for name, args in calls), 1)
                self.assertEqual([args["step"] for name, args in calls if name == "ck3_execute_step"][-1], "pause-map")


class AtomicReportWriteTests(unittest.TestCase):
    def test_enospc_keeps_last_complete_report_and_each_failed_partial(self):
        import errno
        import run_ck3_12002_mcp_live as harness
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            original = b'{"status":"RUNNING","phase":"last-complete"}\n'
            output.write_bytes(original)
            original_open = Path.open

            class FullDiskStream:
                def __init__(self, stream):
                    self.stream = stream
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    self.stream.close()
                def write(self, value):
                    self.stream.write(value[:13])
                    self.stream.flush()
                    raise OSError(errno.ENOSPC, "injected full disk")

            def injected_open(path, *args, **kwargs):
                stream = original_open(path, *args, **kwargs)
                if path.name.startswith(".report.json.partial-") and args and args[0] == "x":
                    return FullDiskStream(stream)
                return stream

            preserved = {}
            with mock.patch.object(Path, "open", injected_open):
                for attempt in range(2):
                    with self.assertRaises(OSError) as failure:
                        harness.write_atomic_report(output, {"status": "RED", "attempt": attempt})
                    self.assertEqual(failure.exception.errno, errno.ENOSPC)
                    context = failure.exception.ck3_write_error_context
                    self.assertEqual(context["operation"], "write-report-json")
                    self.assertEqual(context["report_path"], str(output))
                    self.assertIn("injected full disk", context["original_exception_traceback"])
                    self.assertEqual(output.read_bytes(), original)
                    partials = list(Path(directory).glob(".report.json.partial-*"))
                    self.assertEqual(len(partials), attempt + 1)
                    for partial in partials:
                        self.assertGreater(partial.stat().st_size, 0)
                        if partial in preserved:
                            self.assertEqual(partial.read_bytes(), preserved[partial])
                        preserved[partial] = partial.read_bytes()
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")),
                             {"status": "RUNNING", "phase": "last-complete"})

    def test_success_flushes_and_syncs_before_atomic_json_replacement(self):
        import run_ck3_12002_mcp_live as harness
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            original = b'{"status":"RUNNING","phase":"before"}\n'
            output.write_bytes(original)
            intended = {"status": "RED", "error": "真实错误", "steps": [{"ok": False}]}
            real_fsync, real_replace = os.fsync, os.replace
            events = []

            def synced(fd):
                self.assertEqual(output.read_bytes(), original)
                events.append("fsync")
                return real_fsync(fd)

            def installed(partial, target):
                self.assertEqual(events, ["fsync"])
                self.assertEqual(output.read_bytes(), original)
                self.assertEqual(Path(partial).parent, output.parent)
                self.assertEqual(json.loads(Path(partial).read_text(encoding="utf-8")), intended)
                events.append("replace")
                return real_replace(partial, target)

            with mock.patch.object(harness.os, "fsync", side_effect=synced), \
                    mock.patch.object(harness.os, "replace", side_effect=installed):
                harness.write_atomic_report(output, intended)
            self.assertEqual(events, ["fsync", "replace"])
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), intended)
            self.assertEqual(list(Path(directory).glob(".report.json.partial-*")), [])

    def test_transient_windows_denial_retries_the_same_synced_complete_partial(self):
        import run_ck3_12002_mcp_live as harness
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            original = b'{"status":"RUNNING","phase":"last-complete"}\n'
            output.write_bytes(original)
            intended = {"status": "RED", "error": "真实替换错误", "steps": [{"ok": False}]}
            real_replace = os.replace
            partials = []

            def installed(partial, target):
                partials.append(Path(partial))
                self.assertEqual(output.read_bytes(), original)
                self.assertEqual(json.loads(Path(partial).read_text(encoding="utf-8")), intended)
                self.assertEqual(sync.call_count, 1)
                if len(partials) <= 3:
                    failure = PermissionError("injected Windows replacement denial")
                    failure.winerror = (5, 32, 33)[len(partials) - 1]
                    raise failure
                return real_replace(partial, target)

            with mock.patch.object(harness.os, "name", "nt"), \
                    mock.patch.object(harness.os, "fsync", wraps=os.fsync) as sync, \
                    mock.patch.object(harness.os, "replace", side_effect=installed) as replace, \
                    mock.patch.object(harness.time, "sleep") as sleep:
                harness.write_atomic_report(output, intended)
            self.assertEqual(replace.call_count, 4)
            self.assertEqual(len(set(partials)), 1)
            self.assertEqual(sleep.call_args_list, [mock.call(0.05)] * 3)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), intended)
            self.assertEqual(list(Path(directory).glob(".report.json.partial-*")), [])

    def test_permanent_windows_denial_is_bounded_and_keeps_both_complete_files(self):
        import errno
        import run_ck3_12002_mcp_live as harness
        failures = [(PermissionError("injected persistent denial"), 5, 20),
                    (PermissionError("injected unrelated Windows denial"), 87, 1),
                    (OSError(errno.ENOSPC, "injected replacement disk full"), None, 1)]
        for failure, winerror, limit in failures:
            with self.subTest(winerror=winerror, attempts=limit), tempfile.TemporaryDirectory() as directory:
                if winerror is not None:
                    failure.winerror = winerror
                output = Path(directory) / "report.json"
                original = b'{"status":"RUNNING","phase":"last-complete"}\n'
                output.write_bytes(original)
                intended = {"status": "RED", "error": "实际失败保持红色"}
                partials = []

                def denied(partial, target):
                    partials.append(Path(partial))
                    self.assertEqual(output.read_bytes(), original)
                    self.assertEqual(json.loads(Path(partial).read_text(encoding="utf-8")), intended)
                    self.assertEqual(sync.call_count, 1)
                    raise failure

                with mock.patch.object(harness.os, "name", "nt"), \
                        mock.patch.object(harness.os, "fsync", wraps=os.fsync) as sync, \
                        mock.patch.object(harness.os, "replace", side_effect=denied) as replace, \
                        mock.patch.object(harness.time, "sleep") as sleep:
                    with self.assertRaises(type(failure)) as raised:
                        harness.write_atomic_report(output, intended)
                self.assertIs(raised.exception, failure)
                context = failure.ck3_write_error_context
                self.assertEqual(context["operation"], "replace-report-from-partial")
                self.assertEqual(context["sink_path"], str(output))
                self.assertEqual(context["partial_path"], str(partials[0]))
                self.assertTrue(failure.__notes__)
                self.assertEqual(replace.call_count, limit)
                self.assertEqual(sleep.call_args_list, [mock.call(0.05)] * (limit - 1))
                self.assertEqual(len(set(partials)), 1)
                self.assertEqual(output.read_bytes(), original)
                preserved = list(Path(directory).glob(".report.json.partial-*"))
                self.assertEqual(preserved, [partials[0]])
                self.assertEqual(json.loads(preserved[0].read_text(encoding="utf-8")), intended)

    def test_execute_keeps_finished_advance_and_stops_followup_on_report_sync_fault(self):
        import errno
        import run_ck3_12002_mcp_live as harness
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            report = {"phase": "hold", "steps": []}
            args = Namespace(output=output)
            client = PlanClient(None, args, report, lambda: harness.write_atomic_report(output, report))
            client.advance = mock.AsyncMock(return_value={"elapsed_hours": 24})
            client.fresh = mock.AsyncMock(return_value={"date_raw": 124, "paused": True})
            client.invoke = mock.AsyncMock(side_effect=AssertionError("followup must remain undispatched"))
            failure = OSError(errno.ENOSPC, "injected finished-step report sync fault")
            real_fsync = os.fsync
            sync_count = 0

            def synced(fd):
                nonlocal sync_count
                sync_count += 1
                if sync_count == 2:
                    raise failure
                return real_fsync(fd)

            with mock.patch.object(harness.os, "fsync", side_effect=synced), \
                    mock.patch.object(harness.os, "replace", wraps=os.replace) as replaced:
                with self.assertRaises(OSError) as raised:
                    asyncio.run(client.execute([
                        {"id": "advance-D3-once", "kind": "advance_day", "days": 1},
                        {"id": "next-D3-frame", "tool": "NO_DISPATCH"},
                    ]))
            self.assertIs(raised.exception, failure)
            client.advance.assert_awaited_once()
            client.fresh.assert_awaited_once()
            client.invoke.assert_not_awaited()
            self.assertEqual(sync_count, 2)
            self.assertEqual(replaced.call_count, 1)
            self.assertEqual(len(report["steps"]), 1)
            last = report["steps"][0]
            self.assertIs(last["ok"], True)
            self.assertTrue(last["finished_at"])
            self.assertNotIn("error", last)
            context = failure.ck3_write_error_context
            self.assertEqual(context["operation"], "fsync-report-partial")
            self.assertEqual(context["phase"], "hold")
            self.assertEqual(context["last_step_id"], "advance-D3-once")
            self.assertIs(context["last_step_ok"], True)
            self.assertEqual(context["last_step_finished_at"], last["finished_at"])
            self.assertFalse(json.loads(output.read_text(encoding="utf-8"))["steps"][0]["ok"])
            preserved = list(Path(directory).glob(".report.json.partial-*"))
            self.assertEqual(len(preserved), 1)
            self.assertEqual(json.loads(preserved[0].read_text(encoding="utf-8")), report)


class FixtureStartupNoticeTests(unittest.TestCase):
    """Reduced actual a78 frames/root; typed intro response is an offline fixture."""

    def setUp(self):
        import sys
        from copy import deepcopy
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
        from xar_autoplayer.bridge.version_identity import CK3_12003
        from PIL import Image
        self.copy = deepcopy
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        state_dir = Path(temporary.name)
        profile = state_dir / "profile"
        declared = ["dlc_load.json", "mod/fixture.mod", "mod/product.mod", "pdx_settings.txt",
            "player/game_rules/presets.txt", "tutorial.txt"]
        for relative in declared:
            path = profile / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(relative, encoding="utf-8")
        (state_dir / "preparation.json").write_text(json.dumps({"profile_dir": str(profile),
            "profile_files": {relative: {} for relative in declared}}), encoding="utf-8")
        self.args = Namespace(state_dir=state_dir, output=state_dir / "native-report.json")
        capture = mock.patch("pyautogui.screenshot", return_value=Image.new("RGB", (16, 12)))
        self.capture = capture.start()
        self.addCleanup(capture.stop)
        self.policy = {"required_log_markers": ["XCA: TEST PASS celestial_government_allows_barter",
            "XCA: TEST PASS switched_to_song_emperor"], "forbidden_log_markers": ["XCA: TEST FAIL", "XCA120: TEST FAIL"],
            "post_start": {"government_key": "celestial_government", "primary_title_tier_key": "hegemony", "independent": True}}
        self.submission = {"schema": "ck3-frontend-fixture-robert-start-submission-v1", "schema_version": 1,
            "status": "acknowledged_verification_pending", "accepted": True, "pre_start_identity_proven": True,
            "postcondition_verified": False, "fixture_target_identity_proven": False,
            "requested_character_name_key": "bookmark_rags_to_riches_duke_robert", "uses_ocr": False,
            "uses_keyboard": False, "uses_mouse": False, "binding": {"bridge_pid": 12492, "connection_generation": 1},
            "selected_candidate": {"schema": "ck3-frontend-selected-1066-feudal-candidate-v1", "status": "ready",
                "read_only": True, "selected_bookmark_key": "bm_1066_rags_to_riches",
                "selected_character_name_key": "bookmark_rags_to_riches_duke_robert",
                "selected_character_government_key": "feudal_government", "selected_bookmark_start_date_raw": 53144328},
            "acknowledgement": {"step": "activate-frontend-start-selected-bookmark-v1", "accepted": True,
                "status": "acknowledged_verification_pending", "backend_id": "native-headless"}}
        self.before = {"snapshot_id": "native:3", "revision": 4, "native_revision": 3,
            "date_raw": 53144328, "local_player_id": 1, "episode_projection": "native_campaign", "map_ready": True, "paused": True,
            "played_character": {"character_id": 34422, "alive": True, "source": "native"},
            "active_event": {"source": "native", "instance_id": 1, "option_count": 1,
                "options": [{"index": 0, "option_number": 1, "enabled": True}]},
            "diagnostics": {**self.submission["binding"],
                "hello": {"expected_ck3_version": CK3_12003.game_version, "expected_ck3_sha256": CK3_12003.executable_sha256},
                "last_heartbeat": {"pid": 12492, "main_thread_query_mailbox_v1": {"ready": True,
                    "stamp_read_success": True, "pump_epochs": 36615, "owner_verified_pump_epochs": 36615,
                    "owner_tid": 21528, "current_tid": 21528},
                    "snapshot_observer_12002": {"started_ms": 1, "completed_ms": 0, "read_in_progress": True}}}}
        self.after = deepcopy(self.before)
        self.after.update(snapshot_id="native:4", revision=5, native_revision=4, active_event=None)
        self.root = {"backend_id": "native-headless", "campaign_root_context_ready": True,
            "provenance": {"game_version": CK3_12003.game_version, "executable_sha256": CK3_12003.executable_sha256},
            "queried_snapshot_id": "native:4", "queried_revision": 5, "queried_native_revision": 4, "date_raw": 53144328,
            "player_character_id": 34422, "player_character_alive": True, "government": {"key": "celestial_government"},
            "primary_title": {"title_id": 14022, "tier_raw": 6, "tier_key": "hegemony"},
            "independent": True, "top_liege_character_id": 34422, "immediate_liege_character_id": None}
        self.context = {"schema": "current-event-window-context-v1", "schema_version": 1, "status": "available",
            "window_match_count": 1, "event_definition_key": "tgp_dynastic_cycle.0051", "current_event_instance_id": 1,
            "snapshot_revision": 3, "date_raw": 53144328, "saved_scopes": [],
            "provenance": {"backend_id": CK3_12003.backend_id("event-window-v1")},
            "root_scope": {"status": "available", "type_key": "character", "typed_identity": {
                "status": "available", "kind": "character", "character_id": 34422}},
            "options": [{"rendered_index": 0, "native_option_index": 0, "shown": True,
                "enabled": True, "fallback": False, "cancel": False}]}

    def client(self, *, unknown=False, lost_ack=False):
        from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1
        case = self
        class Client:
            def __init__(self):
                self.calls, self.frames, self.selected = [], 0, False
                self.args = case.args
                self.context_query_frame = None
            async def fresh(self):
                self.frames += 1
                snap = case.copy(case.after if self.selected else case.before)
                heartbeat = snap["diagnostics"]["last_heartbeat"]
                epoch = (125023 if self.selected else 36615) + self.frames * 30
                heartbeat["main_thread_query_mailbox_v1"].update(pump_epochs=epoch, owner_verified_pump_epochs=epoch)
                heartbeat["snapshot_observer_12002"].update(started_ms=self.frames,
                    completed_ms=self.frames if self.frames > 1 else 0, read_in_progress=self.frames == 1)
                return snap
            async def call(self, name, arguments):
                self.calls.append((name, case.copy(arguments)))
                if name == "ck3_query_engine_log_literals_v1":
                    return {"schema": "xar.ck3.engine-log-literals/v1", "log_name": "debug.log", "exists": True,
                        "read_only": True, "case_sensitive": True, "matches": [{"literal": key, "line_count":
                            int(key in case.policy["required_log_markers"])} for key in arguments["literals"]]}
                if name == "ck3_query_current_event_window_context_v1":
                    self.context_query_frame = self.frames
                    context = case.copy(case.context)
                    if unknown:
                        context["event_definition_key"] = "unreviewed.actual.event"
                    return {"status": "available", "current_event_window_context_ready": True,
                        "queried_snapshot_id": "native:3", "queried_revision": 4, "queried_native_revision": 3,
                        "current_event_window_context": context}
                if name == "ck3_query_vanilla_event_knowledge_v1":
                    return query_vanilla_event_knowledge_v1(**arguments)
                if name == "ck3_select_event_option":
                    self.selected = True
                    if lost_ack:
                        raise RuntimeError("normal callback response lost")
                    return {"accepted": True}
                if name == "ck3_query_campaign_root_context_v1":
                    return case.copy(case.root)
                raise AssertionError(name)
        return Client()

    def test_actual_readiness_path_acknowledges_intro_before_original_owner_and_business_gates(self):
        import run_ck3_12002_mcp_live as harness
        client, report = self.client(), {}
        result = asyncio.run(harness.wait_for_fixture_business_context(client, self.policy, self.submission,
            report=report, write=lambda: None, timeout=10, poll_interval=0))
        names = [name for name, arguments in client.calls]
        self.assertEqual(result["status"], "ACTUAL_FIXTURE_QUALIFIED_BUSINESS_CONTEXT_BOUND")
        self.assertEqual(names.count("ck3_select_event_option"), 1)
        self.assertLess(names.index("ck3_query_engine_log_literals_v1"), names.index("ck3_query_current_event_window_context_v1"))
        self.assertLess(names.index("ck3_select_event_option"), names.index("ck3_query_campaign_root_context_v1"))
        self.assertEqual(result["startup_notice"]["status"], "NORMAL_OPTION_EVENT_GONE_OBSERVED")
        self.assertEqual(client.context_query_frame, 3)
        startup = result["first_startup_query_admission"]
        self.assertGreater(startup["current_frame"]["pump_epoch"], startup["previous_frame"]["pump_epoch"])
        self.assertEqual(startup["current_frame"]["owner_tid"], startup["previous_frame"]["owner_tid"])
        self.assertEqual(startup["current_frame"]["event_instance_id"], 1)
        notice = result["startup_notice"]
        self.assertEqual(self.capture.call_count, 2)
        self.assertEqual(notice["before_evidence"]["screenshot"]["size"], [16, 12])
        self.assertEqual(len(notice["before_evidence"]["declared_profile_files"]), 6)
        self.assertEqual(notice["before_evidence"]["declared_profile_files"], notice["after_evidence"]["declared_profile_files"])
        self.assertEqual(notice["before_evidence"]["declared_profile_files"]["tutorial.txt"]["sha256"],
            hashlib.sha256(b"tutorial.txt").hexdigest())
        self.assertFalse(notice["after_evidence"]["intro_character_flag_file_readback"]["proven"])
        self.assertFalse(notice["after_evidence"]["used_for_selection_or_acceptance"])
        self.assertEqual(notice["visible_buttons_before"][0]["native_option_index"], 0)
        self.assertEqual(notice["visible_buttons_after"], [])
        admission = result["first_whole_root_query_admission"]
        self.assertGreater(admission["current_frame"]["pump_epoch"], admission["previous_frame"]["pump_epoch"])
        self.assertEqual(result["binding"]["actor_character_id"], 34422)
        self.assertEqual(result["binding"]["government_key"], "celestial_government")
        self.assertFalse(result["product_acceptance_proven"])
        self.assertFalse(result["start_resubmitted"])
        self.assertFalse(result["fixture_target_identity_proven"])

    def test_unreviewed_actual_event_reaches_failure_hold_without_selection_or_root_query(self):
        import run_ck3_12002_mcp_live as harness
        client, report = self.client(unknown=True), {}
        with self.assertRaisesRegex(RuntimeError, "registry-reviewed acknowledgement"):
            asyncio.run(harness.wait_for_fixture_business_context(client, self.policy, self.submission,
                report=report, write=lambda: None, timeout=10, poll_interval=0))
        names = [name for name, arguments in client.calls]
        self.assertNotIn("ck3_select_event_option", names)
        self.assertNotIn("ck3_query_campaign_root_context_v1", names)
        self.assertEqual(report["frontend_fixture_business_context"]["status"], "FAILED_AFTER_SINGLE_START_NO_RETRY")
        self.assertEqual(self.capture.call_count, 1)

    def test_lost_normal_option_response_keeps_once_marker_and_does_not_replay(self):
        import run_ck3_12002_mcp_live as harness
        client, state = self.client(lost_ack=True), {}
        with self.assertRaisesRegex(RuntimeError, "response lost"):
            asyncio.run(harness.acknowledge_fixture_startup_notice(client, self.before, self.submission, state=state, write=lambda: None))
        with self.assertRaisesRegex(RuntimeError, "cannot be replayed"):
            asyncio.run(harness.acknowledge_fixture_startup_notice(client, self.before, self.submission, state=state, write=lambda: None))
        self.assertEqual([name for name, arguments in client.calls].count("ck3_select_event_option"), 1)
        self.assertTrue(state["startup_notice"]["selection_attempted"])
        self.assertIn("after_evidence", state["startup_notice"])
        self.assertIn("after_native_state_unavailable", state["startup_notice"])
        self.assertNotIn("after_snapshot", state["startup_notice"])
        self.assertEqual(self.capture.call_count, 2)


if __name__ == "__main__":
    unittest.main()
