"""Fixed-input contract tests over real service/MCP paths; no desktop is touched."""
from __future__ import annotations

import asyncio
import copy
import ctypes
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import ck3_clock_pause_mcp as pause
from test_ck3_native_profile_mcp import Backend, fixture


def profile_fixture(root):
    profile, original = fixture(root)
    guard = copy.deepcopy(profile["guard"])
    guard.pop("profile_sha256")
    executable = root / "installation/binaries/ck3.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(Path(guard["target"]["executable"]).read_bytes())
    guard["target"]["executable"] = str(executable)
    guard_path = Path(profile["guard_profile"])
    guard_path.write_text(json.dumps(guard), encoding="utf-8")
    shortcuts = root / "installation/game/gui/shortcuts.shortcuts"
    shortcuts.parent.mkdir(parents=True)
    shortcuts.write_text('# fixture installed source\npause = "SPACE"\nspeed_5 = "5"\n', encoding="utf-8")
    raw = json.loads(original.read_text(encoding="utf-8"))
    for key in ("state_directory", "dll", "injector"):
        raw.pop(key)
    raw["guard_profile_sha256"] = pause.native.desktop.sha256(guard_path)
    raw["pause_shortcut_sha256"] = pause.native.desktop.sha256(shortcuts)
    path = root / "clock-pause-profile.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return pause.load_profile(path), path, shortcuts


class PauseBackend(Backend):
    def __init__(self, profile):
        super().__init__(profile)
        self.clock.update(local_player_id=1, played_character_id=42, process_access=0x410,
            source_contract={"executable_sha256": profile["guard"]["target"]["executable_sha256"],
                "header_sha256": "b"*64, "source_sha256": "c"*64, "reader_sha256": "d"*64})
        self.keys = {key: False for key in ("shift", "control", "alt", "left_windows", "right_windows", "space")}
        self.inputs = 0
        self.after_reads = 0
        self.materialize_after = 1
        self.input_error = False
        self.after_input = None
        self.langid = 0x0409

    def key_state(self):
        return copy.deepcopy(self.keys)

    def keyboard_langid(self, profile):
        return self.langid

    def capture(self, path):
        return self.desktop.capture(path)

    def press_pause(self):
        self.inputs += 1
        if self.after_input is not None:
            self.after_input()
        if self.input_error:
            raise RuntimeError("fixed input delivery unresolved")

    def read_clock(self, profile):
        if self.inputs:
            self.after_reads += 1
            if self.materialize_after is not None and self.after_reads >= self.materialize_after:
                self.clock["paused"] = True
        return super().read_clock(profile)


class PauseTests(unittest.TestCase):
    def make_service(self, root):
        profile, path, shortcuts = profile_fixture(root)
        backend = PauseBackend(profile)
        service = pause.ClockPauseProfileService(profile, backend=backend)
        service.pause_timeout_seconds = .15
        service.pause_poll_seconds = .001
        return service, backend, path, shortcuts

    def test_already_paused_has_zero_inputs_and_own_receipt_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, _ = self.make_service(Path(temporary))
            result = service.pause()
            self.assertEqual(result["status"], "gameplay_pause_verified", result)
            self.assertEqual(result["input_dispatch_attempts"], 0)
            self.assertEqual(backend.inputs, 0)
            self.assertEqual(backend.injections, [])
            self.assertTrue(result["clock_after"]["paused"])
            self.assertEqual(result["schema"], pause.SCHEMA)
            self.assertNotIn("pipe_name", result)
            self.assertEqual(json.loads(Path(result["receipt_path"]).read_text()), result)

    def test_late_pause_reads_until_true_after_exactly_one_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, _ = self.make_service(Path(temporary))
            backend.clock["paused"] = False
            backend.materialize_after = 3
            elapsed = [0.0]
            def advance(seconds):
                elapsed[0] += seconds
            clock = SimpleNamespace(monotonic=lambda: elapsed[0], sleep=advance)
            with patch.object(pause, "time", clock):
                result = service.pause()
            self.assertEqual(result["status"], "gameplay_pause_verified", result)
            self.assertEqual(backend.inputs, 1)
            self.assertGreaterEqual(backend.after_reads, 3)
            self.assertFalse(result["clock_before"]["paused"])
            self.assertTrue(result["clock_after"]["paused"])
            self.assertEqual(set(result["captures"]), {"before", "after"})
            for capture in result["captures"].values():
                self.assertEqual(pause.native.desktop.sha256(Path(capture["path"])), capture["sha256"])

    def test_timeout_and_unresolved_delivery_are_preserved_without_retry(self):
        for input_error in (False, True):
            with self.subTest(input_error=input_error), tempfile.TemporaryDirectory() as temporary:
                service, backend, _, _ = self.make_service(Path(temporary))
                backend.clock["paused"] = False
                backend.materialize_after = None
                backend.input_error = input_error
                result = service.pause()
                self.assertEqual(result["status"], "RED")
                self.assertEqual(backend.inputs, 1)
                self.assertIs(service.pause(), result)
                self.assertEqual(backend.inputs, 1)
                self.assertFalse(result["clock_after"]["paused"]) if not input_error else self.assertIsNone(result["clock_after"])

    def test_unknown_or_mismatched_clock_issues_zero_inputs(self):
        for changes in ({"paused": None}, {"paused": 0}, {"date_raw": 0}, {"speed": 0},
                        {"played_character_id": -1}, {"local_player_id": -1}, {"process_access": 0x1F0FFF},
                        {"source_contract": {"executable_sha256": "0"*64}}):
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as temporary:
                service, backend, _, _ = self.make_service(Path(temporary))
                backend.clock.update({"paused": False, **changes})
                self.assertEqual(service.pause()["status"], "RED")
                self.assertEqual(backend.inputs, 0)

    def test_process_offline_foreground_lease_and_userdir_guards_issue_zero_inputs(self):
        for overrides in ({"pid": 99}, {"process_create_time": 0.0}, {"executable_sha256": "0"*64},
                          {"build_id": "different"}, {"steam_offline_flags": ["0"]},
                          {"steam_client_create_time": 0.0}, {"steam_create_time": 0.0},
                          {"screen_owners": ["other"]}, {"screen_lease_fresh": False},
                          {"focus": {"foreground_hwnd": 999, "foreground_pid": 11}}):
            with self.subTest(overrides=overrides), tempfile.TemporaryDirectory() as temporary:
                service, backend, _, _ = self.make_service(Path(temporary))
                backend.clock["paused"] = False
                backend.desktop.overrides.update(overrides)
                self.assertEqual(service.pause()["status"], "RED")
                self.assertEqual(backend.inputs, 0)
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, _ = self.make_service(Path(temporary))
            backend.command_line = ["ck3.exe", "-userdir=other"]
            self.assertEqual(service.pause()["status"], "RED")
            self.assertEqual(backend.inputs, 0)

    def test_unknown_or_held_key_state_issues_zero_inputs(self):
        for keys in ({}, {"space": None}, {"control": True}):
            with self.subTest(keys=keys), tempfile.TemporaryDirectory() as temporary:
                service, backend, _, _ = self.make_service(Path(temporary))
                backend.clock["paused"] = False
                if keys.get("control"):
                    backend.keys.update(keys)
                else:
                    backend.keys = keys
                self.assertEqual(service.pause()["status"], "RED")
                self.assertEqual(backend.inputs, 0)

    def test_shortcut_mismatch_or_ambiguity_is_rejected(self):
        for text in ('pause = "RETURN"\n', 'pause = "SPACE"\npause = "SPACE"\n'):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as temporary:
                service, backend, path, shortcuts = self.make_service(Path(temporary))
                shortcuts.write_text(text, encoding="utf-8")
                self.assertEqual(service.pause()["status"], "RED")
                self.assertEqual(backend.inputs, 0)
                raw = json.loads(path.read_text())
                raw["pause_shortcut_sha256"] = pause.native.desktop.sha256(shortcuts)
                path.write_text(json.dumps(raw))
                with self.assertRaisesRegex(RuntimeError, "uniquely bind"):
                    pause.load_profile(path)

    def test_new_crash_after_input_retains_red_and_never_replays(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, _ = self.make_service(Path(temporary))
            backend.clock["paused"] = False
            def crash():
                directory = Path(service.profile["userdir"]) / "crashes/new"
                directory.mkdir(parents=True)
            backend.after_input = crash
            result = service.pause()
            self.assertEqual(result["status"], "RED")
            self.assertIn("crash artifact", result["reason"])
            self.assertEqual(backend.inputs, 1)
            self.assertIs(service.pause(), result)
            with self.assertRaisesRegex(RuntimeError, "crash artifact"):
                service.clock()

    def scan_driver(self, acknowledgements):
        events = []
        user = Mock()
        counts = iter(acknowledgements)
        def send(count, pointer, size):
            event = ctypes.cast(pointer, ctypes.POINTER(pause._SpaceInput)).contents
            keyboard = event.payload.keyboard
            events.append((count, size, event.type, keyboard.virtual_key, keyboard.scan_code,
                keyboard.flags, keyboard.time, keyboard.extra_info))
            return next(counts)
        user.SendInput.side_effect = send
        with patch.object(pause.ctypes, "WinDLL", return_value=user):
            backend = pause.ClockPauseBackend()
        return backend, events

    def test_effective_fixed_driver_uses_only_space_scan_and_one_paired_release(self):
        backend, events = self.scan_driver([1, 1])
        with patch.object(pause.time, "sleep") as wait:
            ack = backend.press_pause()
        self.assertEqual(events, [(1, 40, 1, 0, 57, 8, 0, 0), (1, 40, 1, 0, 57, 10, 0, 0)])
        wait.assert_called_once_with(.05)
        self.assertEqual(ack["input_method"], "fixed-windows-scan-code")
        self.assertFalse(ack["ack_is_business_postcondition"])

    def test_production_keyboard_layout_is_read_from_the_bound_target_thread(self):
        backend, events = self.scan_driver([])
        def target_thread(hwnd, pid):
            self.assertEqual(hwnd, 101)
            ctypes.cast(pid, ctypes.POINTER(ctypes.c_uint32)).contents.value = 202
            return 303
        backend._user.GetWindowThreadProcessId.side_effect = target_thread
        backend._user.GetKeyboardLayout.return_value = 0x04090409
        profile = {"guard": {"target": {"hwnd": 101, "pid": 202}}}
        self.assertEqual(backend.keyboard_langid(profile), 0x0409)
        backend._user.GetKeyboardLayout.assert_called_once_with(303)
        backend._user.GetKeyboardLayout.return_value = None
        with self.assertRaisesRegex(RuntimeError, "unknown"):
            backend.keyboard_langid(profile)
        profile["guard"]["target"]["pid"] = 999
        with self.assertRaisesRegex(RuntimeError, "mismatched"):
            backend.keyboard_langid(profile)
        self.assertEqual(events, [])

    def test_unknown_or_non_english_layout_rejects_without_input(self):
        for langid in (None, 0, 0x0804):
            with self.subTest(langid=langid), tempfile.TemporaryDirectory() as temporary:
                service, backend, _, _ = self.make_service(Path(temporary))
                backend.clock["paused"] = False
                backend.langid = langid
                self.assertEqual(service.pause()["status"], "RED")
                self.assertEqual(backend.inputs, 0)

    def test_scan_driver_ack_rejection_never_retries_a_key_event(self):
        for counts, phase in (([0], "key-down"), ([1, 0], "key-up")):
            with self.subTest(phase=phase):
                backend, events = self.scan_driver(counts)
                with patch.object(pause.time, "sleep"), self.assertRaisesRegex(RuntimeError, phase):
                    backend.press_pause()
                self.assertEqual(len(events), len(counts))
                self.assertTrue(all(event[4] == 57 for event in events))

    def test_scan_driver_releases_once_if_the_pulse_wait_raises(self):
        backend, events = self.scan_driver([1, 1])
        with patch.object(pause.time, "sleep", side_effect=RuntimeError("pulse interrupted")):
            with self.assertRaisesRegex(RuntimeError, "pulse interrupted"):
                backend.press_pause()
        self.assertEqual([event[5] for event in events], [8, 10])

    def test_real_scan_driver_ack_is_not_a_pause_postcondition(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, _ = self.make_service(Path(temporary))
            backend.clock["paused"] = False
            backend.materialize_after = None
            driver, events = self.scan_driver([1, 1])
            def dispatch():
                backend.inputs += 1
                return driver.press_pause()
            backend.press_pause = dispatch
            result = service.pause()
            self.assertEqual(result["status"], "RED")
            self.assertFalse(result["clock_after"]["paused"])
            self.assertEqual(result["input_driver_ack"]["key_down_ack_count"], 1)
            self.assertEqual(result["input_driver_ack"]["key_up_ack_count"], 1)
            self.assertEqual(len(events), 2)
            self.assertIs(service.pause(), result)
            self.assertEqual(len(events), 2)

    def test_real_scan_driver_partial_ack_is_latched_by_service(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, _ = self.make_service(Path(temporary))
            backend.clock["paused"] = False
            driver, events = self.scan_driver([1, 0])
            def dispatch():
                backend.inputs += 1
                return driver.press_pause()
            backend.press_pause = dispatch
            result = service.pause()
            self.assertEqual(result["status"], "RED")
            self.assertIn("key-up", result["reason"])
            self.assertEqual(result["input_dispatch_attempts"], 1)
            self.assertIs(service.pause(), result)
            self.assertEqual(len(events), 2)

    def test_final_key_state_guard_change_rejects_before_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, _ = self.make_service(Path(temporary))
            backend.clock["paused"] = False
            reads = 0
            original = backend.key_state
            def key_state():
                nonlocal reads
                reads += 1
                if reads == 2:
                    backend.desktop.overrides["focus"] = {"foreground_hwnd": 999, "foreground_pid": 99}
                return original()
            backend.key_state = key_state
            result = service.pause()
            self.assertEqual(result["status"], "RED")
            self.assertIn("foreground", result["reason"])
            self.assertEqual(backend.inputs, 0)

    def test_receipt_write_failure_cannot_reopen_consumed_dispatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, _ = self.make_service(Path(temporary))
            backend.clock["paused"] = False
            with patch.object(service, "_receipt", side_effect=OSError("fixture receipt write failed")):
                with self.assertRaises(OSError):
                    service.pause()
            self.assertEqual(backend.inputs, 1)
            retained = service.pause()
            self.assertEqual(retained["status"], "RED")
            self.assertIn("receipt write failed", retained["reason"])
            self.assertNotIn("receipt_path", retained)
            self.assertEqual(backend.inputs, 1)

    def test_source_identity_change_and_backwards_clock_after_input_retain_red(self):
        for mode in ("source", "date"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                service, backend, _, _ = self.make_service(Path(temporary))
                backend.clock["paused"] = False
                def changed():
                    if mode == "source": backend.clock["source_contract"]["reader_sha256"] = "e"*64
                    else: backend.clock["date_raw"] -= 24
                backend.after_input = changed
                result = service.pause()
                self.assertEqual(result["status"], "RED")
                self.assertEqual(backend.inputs, 1)
                self.assertIs(service.pause(), result)

    def test_server_tools_are_closed_and_have_no_attach_or_arbitrary_input(self):
        async def exercise(service, backend):
            from mcp import Client
            async with Client(pause.create_server(service)) as client:
                listed = await client.list_tools()
                self.assertEqual({tool.name for tool in listed.tools}, {
                    "ck3_query_clock_pause_profile_v1", "ck3_read_profile_native_clock_v1", "ck3_pause_profile_gameplay_v1"})
                for tool in listed.tools:
                    self.assertEqual(tool.input_schema.get("properties", {}), {})
                for arguments in ({"pid": 11}, {"key": "space"}, {"session_id": service.session_id}):
                    denied = await client.call_tool("ck3_pause_profile_gameplay_v1", arguments)
                    self.assertTrue(denied.is_error)
                self.assertEqual(backend.inputs, 0)
                actual = await client.call_tool("ck3_pause_profile_gameplay_v1", {})
                self.assertFalse(actual.is_error)
                self.assertEqual(actual.structured_content["status"], "gameplay_pause_verified")
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, _ = self.make_service(Path(temporary))
            asyncio.run(exercise(service, backend))

    def test_policy_consumes_real_official_controller_client_without_replacing_native_client(self):
        from native_campaign_autoplay import CampaignConfig, PAUSE, run
        from test_native_campaign_autoplay import FakeClient
        async def exercise(service, backend, campaign):
            from mcp import Client
            async with Client(pause.create_server(service), cache=None) as controller:
                return await run(campaign, CampaignConfig(start_date="1900.1.1", target_date="1900.1.3",
                    baseline_date_raw=1000, save_directory=campaign.directory,
                    evidence_directory=campaign.directory.parent/"policy", checkpoint_days=1,
                    poll_seconds=.002, postcondition_timeout_seconds=.15), pause_provider=controller)
        with tempfile.TemporaryDirectory() as temporary:
            service, backend, _, _ = self.make_service(Path(temporary))
            saves = Path(service.profile["userdir"])/"save games"
            saves.mkdir()
            campaign = FakeClient(saves)
            campaign.observation = backend.observe(service.profile)
            target = service.profile["guard"]["target"]
            original_frame = campaign.frame
            def frame():
                value = original_frame()
                value["diagnostics"]["bridge_pid"] = target["pid"]
                value["diagnostics"]["hello"]["expected_ck3_sha256"] = target["executable_sha256"]
                return value
            campaign.frame = frame
            def clock(profile):
                return {**copy.deepcopy(backend.clock), "paused": campaign.paused, "date_raw": campaign.raw}
            backend.read_clock = clock
            def fixed_pause():
                backend.inputs += 1
                campaign.paused = True
                campaign.revision += 1
            backend.press_pause = fixed_pause
            result = asyncio.run(exercise(service, backend, campaign))
            self.assertEqual(result["status"], "completed", result)
            self.assertEqual(backend.inputs, 1)
            self.assertFalse(any(name == PAUSE for name, _ in campaign.calls))
            self.assertEqual(backend.injections, [])


if __name__ == "__main__":
    unittest.main()
