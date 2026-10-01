"""Focused contract tests; all input and desktop observations are simulated."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from PIL import Image
import desktop_semantic_action_mcp as actions


def profile_fixture(root: Path) -> tuple[dict, Path]:
    image = root / "reviewed.png"
    Image.new("RGB", (1920, 1080), "navy").save(image)
    executable = root / "ck3.exe"
    executable.write_bytes(b"fixture-executable")
    manifest = root / "appmanifest.acf"
    manifest.write_text('"AppState" { "buildid" "fixture-build" }', encoding="utf-8")
    bus = root / "codex_task_bus.py"
    bus.write_text("# fixture bus", encoding="utf-8")
    offline = root / "offline.json"
    offline.write_text(json.dumps({"schema": "ck3.steam_fresh_desktop_frame.v1", "steam_pid": 15}), encoding="utf-8")
    profile = {
        "schema_version": 1,
        "target": {"pid": 11, "hwnd": 22, "process_create_time": 123.0,
            "executable": str(executable), "executable_sha256": actions.sha256(executable),
            "app_manifest": str(manifest), "build_id": "fixture-build",
            "window_title": "Fixture CK3", "window_class": "SDL_app",
            "window_rect": [0, 0, 1920, 1080]},
        "steam": {"root": str(root), "pid": 15, "process_create_time": 120.0,
            "client_pid": 15, "client_process_create_time": 120.0,
            "offline_evidence": str(offline), "offline_evidence_sha256": actions.sha256(offline),
            "offline_visual_reviewed": True},
        "task_bus_script": str(bus), "task_bus_sha256": actions.sha256(bus),
        "screen_task_id": "fixture-screen", "evidence_directory": str(root / "evidence"),
        "actions": {"select_bookmark_ruler": {"source_image": str(image),
            "source_sha256": actions.sha256(image), "preview_bounds": [10, 20, 960, 360],
            "observed_point": [490, 200], "reviewed_bounds": [480, 190, 30, 30]}},
    }
    path = root / "profile.json"
    path.write_text(json.dumps(profile), encoding="utf-8")
    return actions.load_profile(path), path


class FakeBackend:
    def __init__(self, profile: dict) -> None:
        self.profile = profile
        self.overrides: dict = {}
        self.observations = 0
        self.clicked: list = []
        self.captured: list = []

    def observe(self, profile: dict) -> dict:
        self.observations += 1
        target = profile["target"]
        return {**copy.deepcopy(target), "window_pid": target["pid"], "window_visible": True,
            "focus": {"foreground_hwnd": target["hwnd"], "foreground_pid": target["pid"]},
            "screen_size": [1920, 1080], "mouse_buttons": {"left": False},
            "steam_offline_flags": ["1"], "screen_owners": [profile["screen_task_id"]],
            "steam_pid": profile["steam"]["pid"],
            "steam_create_time": profile["steam"]["process_create_time"],
            "steam_executable": str(Path(profile["steam"]["root"]) / "steam.exe"),
            "steam_client_pid": profile["steam"]["client_pid"],
            "steam_client_create_time": profile["steam"]["client_process_create_time"],
            "steam_client_executable": str(Path(profile["steam"]["root"]) / "steam.exe"),
            "screen_lease_fresh": True, **copy.deepcopy(self.overrides)}

    def image_size(self, path: Path) -> tuple[int, int]:
        return (1920, 1080)

    def capture(self, path: Path) -> dict:
        self.captured.append(path)
        Image.new("RGB", (1920, 1080), "green" if self.clicked else "black").save(path)
        return {"path": str(path), "bytes": path.stat().st_size,
                "sha256": actions.sha256(path), "size": [1920, 1080]}

    def click(self, point: tuple[int, int]) -> None:
        self.clicked.append(point)


class SemanticActionTests(unittest.TestCase):
    def test_cef_ui_host_and_separate_native_client_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile, _ = profile_fixture(Path(temporary))
            profile["steam"].update(client_pid=16, client_process_create_time=119.0)
            backend = FakeBackend(profile)
            backend.overrides["steam_executable"] = str(Path(profile["steam"]["root"]) / "bin" / "cef" / "cef.win64" / "steamwebhelper.exe")
            result = actions.SemanticActionService(profile, backend).execute("select_bookmark_ruler")
            self.assertTrue(result["click_dispatched"])
            self.assertEqual(result["status"], "dispatched_requires_business_readback")

    def test_unknown_ui_host_path_and_dead_or_restarted_client_send_zero_input(self) -> None:
        changes = [
            {"steam_executable": "other/steamwebhelper.exe"},
            {"steam_executable": "other/steam.exe"},
            {"steam_pid": 999}, {"steam_client_pid": 999},
            {"steam_client_create_time": 999.0},
            {"steam_client_executable": "other/steam.exe"},
        ]
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                profile, _ = profile_fixture(Path(temporary))
                backend = FakeBackend(profile)
                backend.overrides = change
                with self.assertRaisesRegex(RuntimeError, "Steam"):
                    actions.SemanticActionService(profile, backend).execute("select_bookmark_ruler")
                self.assertEqual(backend.clicked, [])
                self.assertEqual(backend.captured, [])

    def test_live_cef_host_cannot_continue_when_bound_native_client_died(self) -> None:
        import psutil
        import pyautogui
        with tempfile.TemporaryDirectory() as temporary:
            profile, _ = profile_fixture(Path(temporary))
            profile["steam"].update(client_pid=16, client_process_create_time=119.0)
            game = Mock(pid=11)
            host = Mock(pid=15)
            def processes(pid):
                if pid == 16:
                    raise psutil.NoSuchProcess(pid)
                return {11: game, 15: host}[pid]
            with (patch.object(psutil, "Process", side_effect=processes),
                  patch.object(pyautogui, "click") as click,
                  patch.object(pyautogui, "screenshot") as screenshot):
                with self.assertRaises(psutil.NoSuchProcess):
                    actions.SemanticActionService(profile).execute("select_bookmark_ruler")
                click.assert_not_called()
                screenshot.assert_not_called()

    def test_native_backend_reads_pinned_cli_build_offline_session_and_fresh_lease(self) -> None:
        import psutil
        import pyautogui
        import win32gui
        import win32process
        import desktop_steam_offline_recovery as recovery
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile, _ = profile_fixture(root)
            (root / "config").mkdir()
            (root / "config" / "loginusers.vdf").write_text('"WantsOfflineMode" "1"')
            game = Mock(**{"pid": 11, "exe.return_value": profile["target"]["executable"], "create_time.return_value": 123.0})
            steam = Mock(**{"pid": 15, "exe.return_value": str(root / "steam.exe"), "create_time.return_value": 120.0})
            tasks = [{"task_id": "fixture-screen", "state": "running",
                      "resources": ["ck3-screen:acquired"], "updated_at_utc": datetime.now(timezone.utc).isoformat()}]
            with (patch.object(psutil, "Process", side_effect=lambda pid: {11: game, 15: steam}[pid]),
                  patch.object(win32process, "GetWindowThreadProcessId", return_value=(33, 11)),
                  patch.object(win32gui, "IsWindowVisible", return_value=True),
                  patch.object(win32gui, "GetWindowText", return_value="Fixture CK3"),
                  patch.object(win32gui, "GetClassName", return_value="SDL_app"),
                  patch.object(win32gui, "GetWindowRect", return_value=(0, 0, 1920, 1080)),
                  patch.object(pyautogui, "size", return_value=(1920, 1080)),
                  patch.object(actions.coordinates, "foreground_state", return_value={"foreground_hwnd": 22, "foreground_pid": 11}),
                  patch.object(actions.coordinates, "mouse_button_state", return_value={"left": False}),
                  patch.object(recovery, "task_bus_tasks", return_value=tasks) as query_bus):
                observation = actions.NativeDesktopBackend().observe(profile)
                actions.validate_observation(profile, observation)
                self.assertEqual(observation["build_id"], "fixture-build")
                self.assertTrue(observation["screen_lease_fresh"])
                self.assertEqual(observation["steam_offline_flags"], ["1"])
                query_bus.assert_called_once_with(Path(profile["task_bus_script"]))
                Path(profile["task_bus_script"]).write_text("changed CLI")
                with self.assertRaisesRegex(RuntimeError, "task-bus CLI SHA-256 changed"):
                    actions.NativeDesktopBackend().observe(profile)

    def test_reviewed_click_scales_axes_and_records_dispatch_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile, _ = profile_fixture(Path(temporary))
            backend = FakeBackend(profile)
            service = actions.SemanticActionService(profile, backend)
            result = service.execute("select_bookmark_ruler")
            self.assertEqual(backend.clicked, [(960, 540)])
            self.assertEqual(result["status"], "dispatched_requires_business_readback")
            self.assertFalse(result["business_postcondition_verified"])
            self.assertFalse(result["uses_keyboard"])
            self.assertFalse(result["uses_ocr"])
            self.assertEqual(len(backend.captured), 2)
            self.assertNotEqual(result["capture_before"]["sha256"], result["capture_after"]["sha256"])
            self.assertEqual(json.loads(Path(result["receipt_path"]).read_text())["session_id"], service.session_id)
            self.assertIs(service.execute("select_bookmark_ruler"), result)
            self.assertEqual(len(backend.clicked), 1)

    def test_observed_guard_changes_send_zero_input(self) -> None:
        changes = [
            {"window_pid": 999}, {"window_visible": False}, {"pid": 999},
            {"process_create_time": 124.0}, {"executable_sha256": "0" * 64},
            {"build_id": "other-build"}, {"window_class": "other"},
            {"window_rect": [10, 0, 1930, 1080]},
            {"focus": {"foreground_hwnd": 99, "foreground_pid": 99}},
            {"steam_offline_flags": ["0"]}, {"steam_create_time": 121.0},
            {"screen_owners": ["foreign-owner"]}, {"screen_lease_fresh": False},
            {"mouse_buttons": {"left": True}}, {"screen_size": [1280, 720]},
        ]
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                profile, _ = profile_fixture(Path(temporary))
                backend = FakeBackend(profile)
                backend.overrides = change
                with self.assertRaises(RuntimeError):
                    actions.SemanticActionService(profile, backend).execute("select_bookmark_ruler")
                self.assertEqual(backend.clicked, [])
                self.assertEqual(backend.captured, [])

    def test_profile_extra_fields_or_unreviewed_offline_evidence_are_rejected(self) -> None:
        for mutation in ({"unexpected": 1}, {"steam": {}}):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                _, path = profile_fixture(Path(temporary))
                payload = json.loads(path.read_text())
                payload.update(mutation)
                path.write_text(json.dumps(payload))
                with self.assertRaises(ValueError):
                    actions.load_profile(path)

    def test_source_hash_and_reviewed_region_bind_action(self) -> None:
        for mode in ("hash", "point"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                profile, _ = profile_fixture(Path(temporary))
                backend = FakeBackend(profile)
                action = profile["actions"]["select_bookmark_ruler"]
                if mode == "hash":
                    Path(action["source_image"]).write_bytes(b"changed reviewed image")
                else:
                    action["observed_point"] = [100, 100]
                with self.assertRaises((RuntimeError, ValueError)):
                    actions.SemanticActionService(profile, backend).execute("select_bookmark_ruler")
                self.assertEqual(backend.clicked, [])

    def test_guard_is_reread_after_before_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile, _ = profile_fixture(Path(temporary))
            backend = FakeBackend(profile)
            original = backend.capture
            def capture_then_lose_focus(path):
                result = original(path)
                backend.overrides["focus"] = {"foreground_hwnd": 99, "foreground_pid": 99}
                return result
            backend.capture = capture_then_lose_focus
            result = actions.SemanticActionService(profile, backend).execute("select_bookmark_ruler")
            self.assertEqual(result["status"], "RED")
            self.assertFalse(result["click_dispatched"])
            self.assertEqual(backend.clicked, [])
            self.assertTrue(Path(result["receipt_path"]).is_file())

    def test_readback_failure_preserves_click_and_red_receipt_without_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile, _ = profile_fixture(Path(temporary))
            backend = FakeBackend(profile)
            original = backend.click
            def click_then_resize(point):
                original(point)
                backend.overrides["screen_size"] = [1280, 720]
            backend.click = click_then_resize
            service = actions.SemanticActionService(profile, backend)
            result = service.execute("select_bookmark_ruler")
            self.assertTrue(result["click_dispatched"])
            self.assertEqual(result["status"], "RED")
            self.assertIs(service.execute("select_bookmark_ruler"), result)
            self.assertEqual(len(backend.clicked), 1)


class SemanticActionMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_schema_action_allowlist_and_server_identity(self) -> None:
        from mcp import Client
        with tempfile.TemporaryDirectory() as temporary:
            profile, _ = profile_fixture(Path(temporary))
            backend = FakeBackend(profile)
            service = actions.SemanticActionService(profile, backend)
            async with Client(actions.create_server(service)) as client:
                listed = {tool.name: tool for tool in (await client.list_tools()).tools}
                tool = listed["desktop_execute_action_v1"]
                self.assertEqual(set(tool.input_schema["properties"]), {"action_name"})
                self.assertFalse(tool.input_schema["additionalProperties"])
                rejected = await client.call_tool("desktop_execute_action_v1", {
                    "action_name": "select_bookmark_ruler", "x": 1, "session_id": "spoofed"})
                self.assertTrue(rejected.is_error)
                unknown = await client.call_tool("desktop_execute_action_v1", {"action_name": "other"})
                self.assertTrue(unknown.is_error)
                self.assertEqual(backend.clicked, [])
                inspected = await client.call_tool("desktop_query_action_profile_v1", {})
                self.assertEqual(inspected.structured_content["session_id"], service.session_id)
                result = await client.call_tool("desktop_execute_action_v1", {"action_name": "select_bookmark_ruler"})
                self.assertFalse(result.is_error)
                self.assertEqual(result.structured_content["session_id"], service.session_id)
                self.assertFalse(result.structured_content["business_postcondition_verified"])


if __name__ == "__main__":
    unittest.main()
