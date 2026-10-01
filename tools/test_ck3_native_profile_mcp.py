from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ck3_native_profile_mcp as native
from test_desktop_semantic_action_mcp import FakeBackend, profile_fixture


def fixture(root: Path):
    guard, guard_path = profile_fixture(root)
    userdir = root / "userdir"
    userdir.mkdir()
    dll = root / "xar_ck3_bridge.dll"
    injector = root / "xar_ck3_bridge_injector.exe"
    dll.write_bytes(b"fixture bridge")
    injector.write_bytes(b"fixture injector")
    payload = {"schema_version": 1, "guard_profile": str(guard_path),
               "guard_profile_sha256": native.desktop.sha256(guard_path),
               "userdir": str(userdir), "state_directory": str(root / "state"),
               "evidence_directory": str(root / "evidence"), "game_version": "1.20.0.2",
               "dll": {"path": str(dll), "sha256": native.desktop.sha256(dll)},
               "injector": {"path": str(injector), "sha256": native.desktop.sha256(injector)}}
    path = root / "native-profile.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return native.load_profile(path), path


class Backend:
    def __init__(self, profile):
        self.desktop = FakeBackend(profile["guard"])
        self.injections = []
        self.polls = []
        self.command_line = [profile["guard"]["target"]["executable"], f'-userdir={profile["userdir"]}']
        self.report = {"returncode": 0, "complete_process_tree_proven": True}
        self.clock = {"date_raw": 123456, "paused": True, "speed": 3}

    def observe(self, profile):
        return {**self.desktop.observe(profile["guard"]), "command_line": self.command_line}

    def poll(self, profile):
        self.polls.append(profile["guard"]["screen_task_id"])
        return {"ok": True}

    def inject(self, command):
        self.injections.append(command)
        return SimpleNamespace(report=self.report, error=None)

    def read_clock(self, profile):
        return copy.deepcopy(self.clock)


class Driver:
    def __init__(self, profile):
        target = profile["guard"]["target"]
        self.snapshot = {"date_raw": 123456, "paused": True, "speed": 3, "map_ready": True, "revision": 7,
                         "episode_projection": "native_campaign",
                         "diagnostics": {"bridge_pid": target["pid"], "hello": {
                             "game_adapter_status": "ready", "expected_ck3_version": profile["game_version"],
                             "expected_ck3_sha256": target["executable_sha256"]}}}
        self.closed = False

    def take_snapshot(self):
        return copy.deepcopy(self.snapshot)

    def close(self):
        self.closed = True


def service_fixture(root):
    profile, path = fixture(root)
    backend, driver = Backend(profile), Driver(profile)
    arguments = []
    def factory(pipe, **kwargs):
        arguments.append((pipe, kwargs))
        return driver
    service = native.NativeProfileService(profile, backend=backend, driver_factory=factory)
    return service, backend, driver, arguments, path


class NativeProfileTests(unittest.TestCase):
    def test_attach_starts_server_first_binds_pipe_and_returns_native_readback(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, driver, arguments, _ = service_fixture(Path(temporary))
            result = service.attach()
            self.assertEqual(result["status"], "attached_snapshot_verified")
            self.assertEqual(result["snapshot"]["date_raw"], 123456)
            self.assertEqual(backend.injections[0], [service.profile["injector"]["path"], "--pipe",
                                                   service.pipe_name, "11", service.profile["dll"]["path"]])
            self.assertEqual(arguments[0][0], service.pipe_name)
            self.assertEqual(arguments[0][1]["save_dir"], str(Path(service.profile["userdir"]) / "save games"))
            self.assertEqual(arguments[0][1]["episode_projection"], "native_campaign")
            self.assertEqual(backend.polls, [service.profile["guard"]["screen_task_id"]])
            self.assertIs(result, service.attach())
            self.assertEqual(len(backend.injections), 1)
            self.assertTrue(Path(result["receipt_path"]).is_file())
            self.assertFalse(result["uses_ocr"])
            self.assertFalse(result["uses_desktop_input"])
            readback = service.snapshot()
            self.assertEqual(readback["status"], "native_snapshot_verified")
            self.assertEqual(readback["session_id"], result["session_id"])
            service.close()
            self.assertTrue(driver.closed)

    def test_stale_process_offline_and_lease_guards_send_zero_injector_commands(self):
        for changes in ({"pid": 99}, {"process_create_time": 999.0}, {"build_id": "other"},
                        {"steam_offline_flags": ["0"]}, {"steam_client_create_time": 999.0},
                        {"screen_owners": ["other"]}, {"screen_lease_fresh": False}):
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as temporary:
                service, backend, _, arguments, _ = service_fixture(Path(temporary))
                backend.desktop.overrides.update(changes)
                with self.assertRaises(RuntimeError):
                    service.attach()
                self.assertEqual(backend.injections, [])
                self.assertEqual(arguments, [])

    def test_running_clock_rejects_attach_before_endpoint_or_injector(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, arguments, _ = service_fixture(Path(temporary))
            backend.clock["paused"] = False
            with self.assertRaisesRegex(RuntimeError, "paused initialized"):
                service.attach()
            self.assertEqual(backend.injections, [])
            self.assertEqual(arguments, [])

    def test_userdir_and_artifact_changes_are_denied_before_attach(self):
        for mode in ("userdir", "duplicate_userdir", "dll", "injector", "guard"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                service, backend, _, _, _ = service_fixture(Path(temporary))
                if mode == "userdir":
                    backend.command_line[-1] = "-userdir=other"
                elif mode == "duplicate_userdir":
                    backend.command_line.append(backend.command_line[-1])
                elif mode == "guard":
                    Path(service.profile["guard_profile"]).write_text("changed")
                else:
                    Path(service.profile[mode]["path"]).write_bytes(b"changed")
                with self.assertRaises(RuntimeError):
                    service.attach()
                self.assertEqual(backend.injections, [])

    def test_new_crash_artifact_blocks_attach_and_a_racing_native_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, _, _ = service_fixture(Path(temporary))
            crashes = Path(service.profile["userdir"]) / "crashes"
            crashes.mkdir()
            (crashes / "crash-package").mkdir()
            with self.assertRaisesRegex(RuntimeError, "crash artifact"):
                service.attach()
            self.assertEqual(backend.injections, [])
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, driver, _, _ = service_fixture(Path(temporary))
            service.attach()
            original = driver.take_snapshot
            def read_while_crash_starts():
                crashes = Path(service.profile["userdir"]) / "crashes"
                crashes.mkdir()
                (crashes / "incomplete-crash-package").mkdir()
                return original()
            driver.take_snapshot = read_while_crash_starts
            with self.assertRaisesRegex(RuntimeError, "crash artifact"):
                service.snapshot()

    def test_injector_ack_without_containment_proof_is_red_and_not_replayed(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, _, _ = service_fixture(Path(temporary))
            backend.report["complete_process_tree_proven"] = False
            result = service.attach()
            self.assertEqual(result["status"], "RED")
            self.assertIs(result, service.attach())
            self.assertEqual(len(backend.injections), 1)

    def test_new_server_cannot_replay_attach_into_the_claimed_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, driver, _, _ = service_fixture(Path(temporary))
            self.assertEqual(service.attach()["status"], "attached_snapshot_verified")
            second = native.NativeProfileService(service.profile, backend=backend,
                                                  driver_factory=lambda *args, **kwargs: driver)
            with self.assertRaises(FileExistsError):
                second.attach()
            self.assertEqual(len(backend.injections), 1)

    def test_native_wrong_pid_build_or_unavailable_clock_cannot_verify_attach(self):
        for mode in ("pid", "hash", "version", "adapter", "paused", "projection", "date", "map"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                service, backend, driver, _, _ = service_fixture(Path(temporary))
                if mode == "pid":
                    driver.snapshot["diagnostics"]["bridge_pid"] = 99
                elif mode == "paused":
                    driver.snapshot["paused"] = None
                elif mode == "projection":
                    driver.snapshot["episode_projection"] = "one_life"
                elif mode == "date":
                    driver.snapshot["date_raw"] += 24
                elif mode == "map":
                    driver.snapshot["map_ready"] = False
                else:
                    field = {"hash": "expected_ck3_sha256", "version": "expected_ck3_version", "adapter": "game_adapter_status"}[mode]
                    driver.snapshot["diagnostics"]["hello"][field] = "other"
                with patch.object(native.time, "monotonic", side_effect=[0, 11]):
                    result = service.attach()
                self.assertEqual(result["status"], "RED")
                self.assertIs(result, service.attach())
                self.assertEqual(len(backend.injections), 1)

    def test_closed_profile_rejects_caller_style_identity_and_arbitrary_artifact(self):
        for mode in ("extra", "name", "sha"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                _, path = fixture(Path(temporary))
                payload = json.loads(path.read_text())
                if mode == "extra":
                    payload["session_id"] = "caller"
                elif mode == "name":
                    payload["injector"]["path"] = str(Path(temporary) / "shell.exe")
                else:
                    payload["guard_profile_sha256"] = "0" * 64
                path.write_text(json.dumps(payload))
                with self.assertRaises(ValueError):
                    native.load_profile(path)


class McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_exposes_only_closed_profile_semantics(self):
        from mcp import Client
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, _, _ = service_fixture(Path(temporary))
            async with Client(native.create_server(service)) as client:
                tools = (await client.list_tools()).tools
                self.assertEqual({tool.name for tool in tools}, {
                    "ck3_query_native_profile_v1", "ck3_attach_profile_bridge_v1", "ck3_take_profile_native_snapshot_v1",
                    "ck3_query_profile_event_window_v1", "ck3_set_profile_simulation_v1",
                    "ck3_pause_profile_simulation_v1",
                    "ck3_select_profile_event_option_v1", "ck3_save_profile_checkpoint_v1"})
                for tool in tools:
                    self.assertFalse(tool.input_schema["additionalProperties"])
                    if tool.name in {"ck3_query_native_profile_v1", "ck3_attach_profile_bridge_v1", "ck3_take_profile_native_snapshot_v1", "ck3_pause_profile_simulation_v1"}:
                        self.assertEqual(tool.input_schema["properties"], {})
                simulation = next(tool for tool in tools if tool.name == "ck3_set_profile_simulation_v1")
                self.assertEqual(set(simulation.input_schema["properties"]["action"]["enum"]),
                                 {"pause", "resume", "speed_1", "speed_3", "speed_5"})
                denied = await client.call_tool("ck3_set_profile_simulation_v1", {"action": "observe", "expected_revision": 7})
                self.assertTrue(denied.is_error)
                denied_pause = await client.call_tool("ck3_pause_profile_simulation_v1", {"expected_revision": 7})
                self.assertTrue(denied_pause.is_error)
                rejected = await client.call_tool("ck3_attach_profile_bridge_v1", {"pid": 99, "session_id": "spoof"})
                self.assertTrue(rejected.is_error)
                self.assertEqual(backend.injections, [])
                attached = await client.call_tool("ck3_attach_profile_bridge_v1", {})
                self.assertFalse(attached.is_error)
                self.assertEqual(attached.structured_content["session_id"], service.session_id)
                snapshot = await client.call_tool("ck3_take_profile_native_snapshot_v1", {})
                self.assertEqual(snapshot.structured_content["snapshot"]["date_raw"], 123456)


class OrdinaryGameplayTests(unittest.TestCase):
    def setup_gameplay(self, root):
        service, backend, driver, _, _ = service_fixture(root)
        service.attach()
        calls = []
        class Gameplay:
            def execute_step(self, step, *, expected_revision):
                calls.append((step, expected_revision))
                if step == "resume-map": driver.snapshot["paused"] = False
                elif step == "pause-map": driver.snapshot["paused"] = True
                else: driver.snapshot["speed"] = int(step[-1])
                return {"status": "ACK"}
            def select_event_option(self, option_number, **kwargs):
                calls.append(("event", option_number, kwargs))
                driver.snapshot["active_event"] = None
                return {"status": "ACK"}
            def save_checkpoint(self, **kwargs):
                calls.append(("save", kwargs))
                save_dir = Path(service.profile["userdir"]) / "save games"
                save_dir.mkdir(exist_ok=True)
                path = save_dir / "checkpoint.ck3"
                path.write_bytes(b"native fixture save")
                return {"checkpoint": {"status": "saved", "path": str(path), "size": path.stat().st_size,
                        "sha256": native.desktop.sha256(path), "date_raw": driver.snapshot["date_raw"]}}
            def query_current_event_window_context_v1(self, instance, **kwargs):
                calls.append(("query", instance, kwargs))
                return {"instance_id": instance}
        service._gameplay = Gameplay()
        service._postcondition_timeout_seconds = 0.01
        service._postcondition_poll_seconds = 0.001
        return service, backend, driver, calls

    def test_normal_time_controls_read_actual_postconditions_without_episode_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, calls = self.setup_gameplay(Path(temporary))
            for action in ("resume", "pause", "speed_5"):
                result = service.simulation(action, 7)
                self.assertEqual(result["status"], "native_gameplay_postcondition_verified")
                self.assertTrue(Path(result["receipt_path"]).is_file())
            self.assertEqual(calls, [("resume-map", 7), ("pause-map", 7), ("set-speed-5", 7)])
            self.assertEqual(len(backend.polls), 4) # attach plus three normal actions

    def test_running_pause_binds_current_provider_frame_after_poll_without_replaying(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, driver, calls = self.setup_gameplay(Path(temporary))
            driver.snapshot.update(paused=False, speed=5)
            original_poll = backend.poll
            def advance_during_poll(profile):
                driver.snapshot["revision"] += 1
                driver.snapshot["date_raw"] += 24
                return original_poll(profile)
            backend.poll = advance_during_poll
            with self.assertRaisesRegex(RuntimeError, "expected map-ready"):
                service.simulation("pause", 7)
            self.assertEqual(calls, [])
            result = service.pause_current()
            self.assertEqual(calls, [("pause-map", None)])
            self.assertEqual(result["snapshot_before"]["revision"], 9)
            self.assertFalse(result["snapshot_before"]["paused"])
            self.assertTrue(result["snapshot_after"]["paused"])
            self.assertEqual(result["revision_binding"], "provider_submission_frame")
            self.assertEqual(result["status"], "native_gameplay_postcondition_verified")
            self.assertTrue(Path(result["receipt_path"]).is_file())

    def test_current_pause_guard_or_unready_map_issues_zero_commands(self):
        for mode in ("foreground", "offline", "lease", "userdir", "crash", "map", "poll_guard"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                service, backend, driver, calls = self.setup_gameplay(Path(temporary))
                driver.snapshot["paused"] = False
                if mode == "foreground": backend.desktop.overrides["focus"] = {"foreground_hwnd": 999, "foreground_pid": 999}
                elif mode == "offline": backend.desktop.overrides["steam_offline_flags"] = ["0"]
                elif mode == "lease": backend.desktop.overrides["screen_lease_fresh"] = False
                elif mode == "userdir": backend.command_line[-1] = "-userdir=other"
                elif mode == "crash":
                    directory = Path(service.profile["userdir"]) / "crashes"
                    directory.mkdir()
                    (directory / "incomplete").mkdir()
                elif mode == "map": driver.snapshot["map_ready"] = False
                else:
                    backend.poll = lambda profile: backend.desktop.overrides.update(focus={"foreground_hwnd": 999, "foreground_pid": 999})
                with self.assertRaises(RuntimeError): service.pause_current()
                self.assertEqual(calls, [])

    def test_current_pause_ack_failure_and_crash_readback_are_red_after_one_submission(self):
        for mode in ("ack_only", "crash", "pid", "date_backwards", "timeout"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                service, _, driver, calls = self.setup_gameplay(Path(temporary))
                driver.snapshot["paused"] = False
                def submit(step, *, expected_revision):
                    calls.append((step, expected_revision))
                    if mode == "timeout": raise TimeoutError("fixture command timeout")
                    if mode != "ack_only": driver.snapshot["paused"] = True
                    if mode == "crash":
                        directory = Path(service.profile["userdir"]) / "crashes"
                        directory.mkdir()
                        (directory / "incomplete").mkdir()
                    elif mode == "pid": driver.snapshot["diagnostics"]["bridge_pid"] = 999
                    elif mode == "date_backwards": driver.snapshot["date_raw"] -= 24
                    return {"status": "ACK"}
                service._gameplay.execute_step = submit
                result = service.pause_current()
                self.assertEqual(calls, [("pause-map", None)])
                self.assertEqual(result["status"], "RED")
                self.assertTrue(Path(result["receipt_path"]).is_file())

    def test_event_save_and_resume_keep_exact_revision_after_current_pause(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, _, driver, calls = self.setup_gameplay(Path(temporary))
            driver.snapshot["revision"] = 9
            for operation in (lambda: service.simulation("resume", 7),
                              lambda: service.select_event(1, 123, 7),
                              lambda: service.checkpoint(7)):
                with self.assertRaises(RuntimeError): operation()
            self.assertEqual(calls, [])

    def test_invalid_identity_revision_lease_and_unpaused_save_issue_no_action(self):
        for mode in ("revision", "boolean", "lease", "unpaused", "step"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                service, backend, driver, calls = self.setup_gameplay(Path(temporary))
                if mode == "lease": backend.desktop.overrides["screen_lease_fresh"] = False
                if mode == "unpaused": driver.snapshot["paused"] = False
                with self.assertRaises((ValueError, RuntimeError)):
                    if mode == "step": service.simulation("observe", 7)
                    elif mode == "unpaused": service.checkpoint(7)
                    else: service.simulation("resume", 8 if mode == "revision" else True if mode == "boolean" else 7)
                self.assertEqual(calls, [])

    def test_event_and_checkpoint_require_native_and_file_readback(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, _, driver, calls = self.setup_gameplay(Path(temporary))
            driver.snapshot["active_event"] = {"instance_id": 123}
            queried = service.query_event(123, 7)
            self.assertEqual(queried["result"]["instance_id"], 123)
            selected = service.select_event(1, 123, 7)
            self.assertIsNone(selected["snapshot_after"]["active_event"])
            saved = service.checkpoint(7)
            self.assertEqual(saved["status"], "native_gameplay_postcondition_verified")
            self.assertEqual(saved["result"]["checkpoint"]["date_raw"], 123456)
            self.assertEqual([call[0] for call in calls], ["query", "event", "save"])

    def test_ack_with_unchanged_event_or_missing_save_bytes_is_red(self):
        for mode in ("event", "save", "resume"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                service, _, driver, calls = self.setup_gameplay(Path(temporary))
                driver.snapshot["active_event"] = {"instance_id": 123}
                if mode == "event":
                    service._gameplay.select_event_option = lambda *args, **kwargs: {"status": "ACK"}
                    result = service.select_event(1, 123, 7)
                elif mode == "save":
                    service._gameplay.save_checkpoint = lambda **kwargs: {"checkpoint": {"status": "saved"}}
                    result = service.checkpoint(7)
                else:
                    service._gameplay.execute_step = lambda *args, **kwargs: {"status": "ACK"}
                    result = service.simulation("resume", 7)
                self.assertEqual(result["status"], "RED")
                self.assertTrue(Path(result["receipt_path"]).is_file())


if __name__ == "__main__":
    unittest.main()
