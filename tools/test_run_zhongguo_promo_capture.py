#!/usr/bin/env python3
"""Static contracts for the append-only ZhongGuo promo capture mode."""

from __future__ import annotations

from pathlib import Path
import inspect
import json
import re
import sys
import tempfile
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "tools" / "run_zhongguo_acceptance.py"
FIXTURE = ROOT / "tools" / "fixtures" / "zg361_acceptance"
SCOREBOARD_GUI = ROOT / "mod_zhongguo_style" / "gui" / "zg361_scoreboard.gui"
IDS = (1, 7, 20, 22, 26, 361)


def bom_text(path: Path) -> str:
    data = path.read_bytes()
    assert data.startswith(b"\xef\xbb\xbf"), path
    return data.decode("utf-8-sig")


def main() -> int:
    runner = RUNNER.read_text(encoding="utf-8")
    scenario = re.search(
        r"def run_scenario\(.*?(?=^def )", runner, re.M | re.S
    )
    assert scenario is not None
    body = scenario.group(0)
    assert body.index("initialize_fixture") < body.index("recorder.start()")
    assert body.index("close_native_decisions_panel") < body.index("recorder.start()")
    assert body.index("run_native_title_navigation_matrix") < body.index(
        "recorder.start()"
    )
    assert body.index("assert_promo_frame_clean") < body.index("recorder.start()")
    for token in (
        '"reviewed_official_history_id": reviewed_history_id',
        '"title_navigation_mcp_matrix": title_navigation_evidence',
        '"fixture_constructor_counts": constructor_counts',
        '"historical_subjects_manufactured_by_fixture": bool(',
        '"test_decisions_visible_inside_clean_spans": 0 if recorder else None',
        '"native_decisions_drawer_visible_inside_clean_spans": 0 if recorder else None',
        '"real_character_runtime_attestation": {',
        '"promo_policy_chain": {',
        '"persisted_choices_verified": bool(',
    ):
        assert token in body, token

    for token in (
        '"-f",\n            "gdigrab"',
        '"zg361-promo-live-full-take-01.mkv"',
        '"exclude_ck3_loading": True',
        '"--promo-capture"',
        "capture_received_scoreboard",
        "capture_policy_cards",
    ):
        assert token in runner, token

    scoreboard = re.search(
        r"def capture_scoreboard_gui\(.*?(?=^def )", runner, re.M | re.S
    )
    assert scoreboard is not None
    scoreboard_body = scoreboard.group(0)
    for token in (
        "isolated.ensure_decisions_panel",
        '"考核榜", acceptance.FULL_SCREEN_REGION, contains=False',
        "SCOREBOARD_BUTTON_REGION",
        '"07_scoreboard_hidden_by_right_panel.png"',
        '"right_panel_suppression_ocr": True',
        '"right_panel_suppression_artifact"',
        '"button_center_normalized"',
        '"button_expected_region"',
        "audit_scoreboard_controls",
        '"representative_control_audit"',
    ):
        assert token in scoreboard_body, token
    assert scoreboard_body.index("isolated.ensure_decisions_panel") < scoreboard_body.index(
        "close_native_decisions_panel"
    )
    assert scoreboard_body.index("close_native_decisions_panel") < scoreboard_body.index(
        '"07_scoreboard_button.png"'
    )
    assert 'cockpit_tokens = ("361 制度账本", "证据质量", "组织信任", "预算压力")' in scoreboard_body
    assert "except acceptance.RunnerError:" in scoreboard_body
    cockpit_index = scoreboard_body.index("cockpit_tokens")
    assert cockpit_index < scoreboard_body.index(
        "settle_promo_interruptions", cockpit_index
    )
    assert '"08_scoreboard_cockpit_recovered"' in scoreboard_body

    control_audit = re.search(
        r"def audit_scoreboard_controls\(.*?(?=^def )", runner, re.M | re.S
    )
    assert control_audit is not None
    control_body = control_audit.group(0)
    for token in (
        "SCOREBOARD_TITLE_CLOSE_BUTTON",
        "SCOREBOARD_BACKDROP_POINT",
        "select_representative_scoreboard_row",
        "name_probe = personal_name[-2:]",
        "wait_for_representative_character_view",
        '"generated_total": SCOREBOARD_GENERATED_ROW_LINKS',
        '"live_clicked": 1',
        '"not_individually_clicked": SCOREBOARD_GENERATED_ROW_LINKS - 1',
        '"one representative click over a shared generated row structure"',
        '"scoreboard_reopened_after_character_cleanup": True',
        '"08_gui_audit_row_link_reopen.png"',
    ):
        assert token in control_body, token
    assert control_body.index("settle_promo_interruptions") < control_body.index(
        "performance-board title-bar close button"
    )
    assert control_body.index("performance-board title-bar close button") < control_body.index(
        "performance-board modal backdrop"
    )
    assert control_body.index("performance-board modal backdrop") < control_body.index(
        "representative generated scoreboard row"
    )

    close_character = re.search(
        r"def close_representative_character_view\(.*?(?=^def )",
        runner,
        re.M | re.S,
    )
    assert close_character is not None
    close_character_body = close_character.group(0)
    for token in (
        "CHARACTER_WINDOW_CLOSE_BUTTON",
        "native character title-bar close button",
        '"method": "title_bar_close"',
        "absent_hits >= 2",
    ):
        assert token in close_character_body, token
    assert 'pyautogui.press("escape")' not in close_character_body

    close_drawer = re.search(
        r"def close_native_decisions_panel\(.*?(?=^def )", runner, re.M | re.S
    )
    assert close_drawer is not None
    close_body = close_drawer.group(0)
    for token in (
        'acceptance.pyautogui.press("escape")',
        "DECISIONS_CLOSE_BUTTON",
        "native Decisions title-bar close button",
        "absent_hits >= 2",
        'return "title_bar_close"',
        "park_pointer_away_from_right_rail",
    ):
        assert token in close_body, token
    assert (
        close_body.index("native Decisions title-bar close button")
        < close_body.rindex("park_pointer_away_from_right_rail()")
        < close_body.index('return "title_bar_close"')
    )

    received = re.search(
        r"def capture_received_scoreboard\(.*?(?=^def )", runner, re.M | re.S
    )
    assert received is not None
    received_body = received.group(0)
    assert '"\u8ba4\u547d"' in received_body
    assert '"\u4e0a\u53f8\u8003\u5b9a"' in received_body
    assert (
        'result_option = acceptance.wait_for_ocr_text(\n        "\u77e5\u9053\u4e86"'
        not in received_body
    )
    assert "real 3.25 result response was not accepted" in received_body
    assert "acceptance.ensure_game_paused" in received_body
    assert "settle_promo_interruptions" in received_body
    for token in (
        "arm_native_speed_one(timeline_service)",
        "pause_after_promo_event_click",
        '"11_received_result_immediate_pause_gate.json"',
        'stream.count("ZGA: TEST PASS clean_policy_001_dispatched")',
        '"early_policy_001_marker_count"',
        'pause_evidence["result"] = "RED"',
        '"policy card 001 dispatched before received-scoreboard capture"',
    ):
        assert token in received_body, token
    assert received_body.index("arm_native_speed_one(timeline_service)") < received_body.index(
        'acceptance.deliberate_click(result_option, "accept real 3.25 result")'
    )
    assert received_body.index(
        'acceptance.deliberate_click(result_option, "accept real 3.25 result")'
    ) < received_body.index("pause_after_promo_event_click")
    assert (
        'acceptance.deliberate_click(result_option, "accept real 3.25 result")\n'
        "    pause_evidence = pause_after_promo_event_click("
    ) in received_body
    assert 'acceptance.ensure_game_paused(artifacts, "11_received_result")' not in received_body
    for token in (
        '"本人所属考核单元"',
        '"11_received_tab_reopened"',
        '"received_tab_clicked_live": True',
        '"received_tab_idempotent_reopen_live": True',
        "does not inherit",
    ):
        assert token in received_body, token
    assert '"11_received_cockpit_tab_opened"' not in received_body
    assert received_body.index("open received performance board") < received_body.index(
        '"11_received_after_board_open"'
    )

    scoreboard_capture = scoreboard_body
    for token in (
        'acceptance.pyautogui.press("space")',
        'ensure_hud_date_frozen(artifacts, "07_result_summary_closed")',
        '"07_result_summary_closed_preemption"',
        "isolated.ensure_decisions_panel",
    ):
        assert token in scoreboard_capture, token
    assert scoreboard_capture.index(
        'acceptance.deliberate_click(result_option, "production review result summary")'
    ) < scoreboard_capture.index('acceptance.pyautogui.press("space")')
    assert scoreboard_capture.index(
        'ensure_hud_date_frozen(artifacts, "07_result_summary_closed")'
    ) < scoreboard_capture.index('"07_result_summary_closed_preemption"')
    assert scoreboard_capture.index(
        '"07_result_summary_closed_preemption"'
    ) < scoreboard_capture.index("isolated.ensure_decisions_panel")
    assert received_body.index('"11_received_after_board_open"') < received_body.index(
        "acceptance.wait_for_ocr_tokens"
    )

    interruption = re.search(
        r"def settle_promo_interruptions\(.*?(?=^def )",
        runner,
        re.M | re.S,
    )
    assert interruption is not None
    interruption_body = interruption.group(0)
    for token in (
        "PROMO_INTERRUPTION_MAX_DISMISSALS",
        "allow_succession=True",
        "allow_succession=False",
        "acceptance.quick_recovery_kind",
        "acceptance.write_recovery_bundle",
        'status="blocked_succession"',
        'status="blocked_unknown_modal"',
        'status="blocked_dismissal_limit"',
        '"scope": "promo_fixture_only"',
    ):
        assert token in runner, token
    assert "acceptance.deliberate_click" in interruption_body
    assert "ensure_hud_date_frozen" in interruption_body
    assert "acceptance.ensure_game_paused" not in interruption_body
    assert "selected is None or kind is None" in interruption_body
    assert "len(dismissed) >= max_dismissals" in interruption_body

    sys.path.insert(0, str(ROOT / "tools"))
    import run_zhongguo_acceptance as capture

    arm_source = inspect.getsource(capture.arm_native_speed_one)
    for token in (
        'service.execute_step("set-speed-1")',
        'snapshot.get("speed") == 1',
        'snapshot.get("paused") is True',
        'isinstance(snapshot.get("date_raw"), int)',
    ):
        assert token in arm_source, token
    pause_source = inspect.getsource(capture.pause_after_promo_event_click)
    for token in (
        "transition_deadline = time.monotonic() + 0.75",
        'observed["date_raw"] != pre_date',
        'snapshot.get("paused") is False',
        'service.execute_step("pause-map")',
        'pause_submission.get("status") == "submitted"',
        'all(item["date_raw"] == pre_date for item in tail)',
        "and event_transitioned",
    ):
        assert token in pause_source, token
    assert pause_source.index('snapshot.get("paused") is False') < (
        pause_source.index('service.execute_step("pause-map")')
    )

    class SpeedOneService:
        def __init__(self) -> None:
            self.steps: list[str] = []

        def execute_step(self, step: str) -> dict[str, object]:
            self.steps.append(step)
            return {"step": step, "accepted": True, "status": "submitted"}

        def snapshot(self) -> dict[str, object]:
            return {
                "revision": 1,
                "native_revision": 1,
                "date_raw": 200,
                "paused": True,
                "speed": 1,
                "active_event": {"instance_id": 9},
                "played_character": {"character_id": 77},
            }

    speed_one_service = SpeedOneService()
    speed_one_gate = capture.arm_native_speed_one(speed_one_service)
    assert speed_one_service.steps == ["set-speed-1"]
    assert speed_one_gate["snapshot"]["paused"] is True

    class PromoEventPauseService:
        def __init__(self) -> None:
            self.trace: list[str] = []
            self.snapshots = [
                {
                    "revision": 2,
                    "native_revision": 2,
                    "date_raw": 200,
                    "paused": False,
                    "speed": 1,
                    "active_event": None,
                    "played_character": {"character_id": 77},
                },
                *[
                    {
                        "revision": 3 + index,
                        "native_revision": 3 + index,
                        "date_raw": 200,
                        "paused": True,
                        "speed": 1,
                        "active_event": None,
                        "played_character": {"character_id": 77},
                    }
                    for index in range(3)
                ],
            ]

        def snapshot(self) -> dict[str, object]:
            self.trace.append("snapshot")
            return self.snapshots.pop(0)

        def execute_step(self, step: str) -> dict[str, object]:
            self.trace.append(f"execute:{step}")
            assert step == "pause-map"
            return {"step": step, "accepted": True, "status": "submitted"}

    pre_click = {
        "revision": 1,
        "native_revision": 1,
        "date_raw": 200,
        "paused": True,
        "speed": 1,
        "active_event": {"instance_id": 9},
        "played_character": {"character_id": 77},
    }
    pause_service = PromoEventPauseService()
    with tempfile.TemporaryDirectory() as temp_dir:
        received_pause = capture.pause_after_promo_event_click(
            pause_service,
            Path(temp_dir),
            pre_click,
            stem="mock_received_result",
        )
        assert pause_service.trace[:2] == ["snapshot", "execute:pause-map"]
        assert received_pause["result"] == "GREEN"
        assert received_pause["pause_submission_confirmed"] is True
        assert received_pause["running_transition_seen_same_date"] is True
        assert received_pause["event_transitioned"] is True
        assert received_pause["played_character_stable"] is True
        assert received_pause["last_three_paused_at_pre_click_date"] is True
        assert (
            Path(temp_dir) / "mock_received_result_immediate_pause_gate.json"
        ).is_file()

    class DateDriftPauseService:
        def __init__(self) -> None:
            self.snapshots = [
                {
                    "revision": 2,
                    "native_revision": 2,
                    "date_raw": 201,
                    "paused": False,
                    "speed": 1,
                    "active_event": None,
                    "played_character": {"character_id": 77},
                },
                *[
                    {
                        "revision": 3 + index,
                        "native_revision": 3 + index,
                        "date_raw": 201,
                        "paused": True,
                        "speed": 1,
                        "active_event": None,
                        "played_character": {"character_id": 77},
                    }
                    for index in range(5)
                ],
            ]

        def snapshot(self) -> dict[str, object]:
            return self.snapshots.pop(0)

        def execute_step(self, step: str) -> dict[str, object]:
            return {"step": step, "accepted": True, "status": "submitted"}

    with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
        capture.time,
        "monotonic",
        side_effect=[0, 0, 1, 2, 3, 4, 5, 6, 7],
    ), mock.patch.object(capture.time, "sleep", return_value=None), mock.patch.object(
        capture.acceptance.ImageGrab,
        "grab",
        return_value=SimpleNamespace(save=lambda _path: None),
    ):
        try:
            capture.pause_after_promo_event_click(
                DateDriftPauseService(),
                Path(temp_dir),
                pre_click,
                stem="mock_date_drift",
            )
        except capture.acceptance.RunnerError:
            pass
        else:
            raise AssertionError("date drift must fail the promo-event pause gate")
        drift_gate = json.loads(
            (Path(temp_dir) / "mock_date_drift_immediate_pause_gate.json").read_text(
                encoding="utf-8"
            )
        )
        assert drift_gate["result"] == "RED"
        assert drift_gate["running_transition_seen_same_date"] is False
        assert drift_gate["transition_failure"] == (
            "game date advanced before native pause submission"
        )

    # The runner preflight must follow CK3's authoritative unquoted shortcut
    # syntax.  The generated product passes as-is; replacing both close
    # shortcuts with the formerly accepted quoted spelling must be rejected.
    product_errors = capture.product_source_errors()
    assert product_errors == [], product_errors
    authoritative_gui = bom_text(SCOREBOARD_GUI)
    assert authoritative_gui.count("shortcut = close_window") == 2
    quoted_gui = authoritative_gui.replace(
        "shortcut = close_window", 'shortcut = "close_window"'
    )
    assert quoted_gui != authoritative_gui
    original_read_text = Path.read_text

    def read_text_with_quoted_scoreboard(
        path: Path, *args: object, **kwargs: object
    ) -> str:
        if path.resolve() == SCOREBOARD_GUI.resolve():
            return quoted_gui
        return original_read_text(path, *args, **kwargs)

    with mock.patch.object(Path, "read_text", read_text_with_quoted_scoreboard):
        quoted_errors = capture.product_source_errors()
    assert (
        "production managed scoreboard GUI missing shortcut = close_window"
        in quoted_errors
    ), quoted_errors

    title_navigation = inspect.getsource(
        capture.run_native_title_navigation_matrix
    )
    for token in (
        "title_navigation_live._run_navigation_sequence(service)",
        "title_navigation_live._known_call(",
        'label="final_bianzhou_before_ffmpeg"',
        "title_navigation_live.COUNTY_TITLE_KEY",
        'allowed_statuses={"centered", "already_centered"}',
        '"target_write_blocked"',
        '"typed_matrix_payload_sha256"',
        '"typed_unknown_error_hash"',
        '"zero_visual_or_input_fallback"',
        '"inhibit_positive_explicitly_skipped"',
        '"ffmpeg_started": False',
        '"hkl_scope": "other_existing_gui_operations_only"',
        '"05_title_navigation_mcp_matrix.json"',
    ):
        assert token in title_navigation, token
    for forbidden in (
        "ImageChops",
        "ImageGrab",
        "pyautogui",
        "pyperclip",
        "clipboard",
        "find_ocr_text",
        "wait_for_ocr_text",
        "ocr_results",
        "force_ck3_english_keyboard_layout",
        "deliberate_click",
    ):
        assert forbidden not in title_navigation, forbidden
    assert not hasattr(capture, "recenter_promo_camera_on_player_capital")
    assert "temporary_ocr_compatibility" not in runner
    assert "promo_camera_more_menu_find_title" not in runner
    assert "pyperclip" not in runner
    assert "ImageChops" not in runner

    keyboard_layout = inspect.getsource(capture.force_ck3_english_keyboard_layout)
    for token in (
        "GetGUIThreadInfo",
        "GetKeyboardLayout",
        "GetKeyboardLayoutList",
        "PostMessageW",
        "WM_INPUTLANGCHANGEREQUEST",
        "WINDOWS_ENGLISH_US_HKL",
        '"after_langid"',
        '"restore_requested": False',
        '"restore_performed": False',
        '"left_in_english"',
        '"CK3 lost foreground while changing its keyboard layout"',
    ):
        assert token in keyboard_layout, token

    class FakeWin32Call:
        def __init__(self, implementation):
            self.implementation = implementation
            self.calls = []
            self.argtypes = None
            self.restype = None

        def __call__(self, *args):
            self.calls.append(args)
            return self.implementation(*args)

    keyboard_values = iter((0x08040804, 0x04090409))

    def fake_gui_thread_info(_thread_id, info_pointer):
        info_pointer._obj.hwndFocus = 222
        return 1

    fake_user32 = SimpleNamespace(
        GetGUIThreadInfo=FakeWin32Call(fake_gui_thread_info),
        GetKeyboardLayout=FakeWin32Call(lambda _thread_id: next(keyboard_values)),
        PostMessageW=FakeWin32Call(lambda *_args: 1),
    )
    with tempfile.TemporaryDirectory() as temporary:
        layout_artifacts = Path(temporary)
        with (
            mock.patch.object(capture.os, "name", "nt"),
            mock.patch.object(capture.acceptance, "focus_ck3", return_value=True),
            mock.patch.object(
                capture.acceptance.win32gui,
                "GetForegroundWindow",
                return_value=111,
            ),
            mock.patch.object(
                capture.acceptance.win32gui,
                "GetWindowText",
                return_value="Crusader Kings III",
            ),
            mock.patch.object(
                capture.acceptance.win32process,
                "GetWindowThreadProcessId",
                side_effect=lambda hwnd: (10, 999) if hwnd == 111 else (11, 999),
            ),
            mock.patch.object(capture.acceptance, "ACTIVE_CK3_PID", 999),
            mock.patch.object(
                capture.acceptance.win32api,
                "GetKeyboardLayoutList",
                return_value=[0x04090409, 0x08040804],
            ),
            mock.patch.object(
                capture.ctypes,
                "windll",
                SimpleNamespace(user32=fake_user32),
            ),
        ):
            layout_gate = capture.force_ck3_english_keyboard_layout(
                layout_artifacts, "layout_state_machine"
            )
        assert layout_gate["result"] == "GREEN"
        assert layout_gate["before_hkl"] == "0x08040804"
        assert layout_gate["after_hkl"] == "0x04090409"
        assert layout_gate["input_window_handle"] == 222
        assert layout_gate["input_thread_id"] == 11
        assert layout_gate["message_posted"] is True
        assert layout_gate["restore_requested"] is False
        assert layout_gate["restore_performed"] is False
        assert layout_gate["left_in_english"] is True
        assert fake_user32.PostMessageW.calls == [
            (222, capture.WM_INPUTLANGCHANGEREQUEST, 0, 0x04090409)
        ]
        assert (layout_artifacts / "layout_state_machine.json").is_file()

    already_english_user32 = SimpleNamespace(
        GetGUIThreadInfo=FakeWin32Call(fake_gui_thread_info),
        GetKeyboardLayout=FakeWin32Call(lambda _thread_id: 0x04090409),
        PostMessageW=FakeWin32Call(lambda *_args: 1),
    )
    with tempfile.TemporaryDirectory() as temporary:
        layout_artifacts = Path(temporary)
        with (
            mock.patch.object(capture.os, "name", "nt"),
            mock.patch.object(capture.acceptance, "focus_ck3", return_value=True),
            mock.patch.object(
                capture.acceptance.win32gui,
                "GetForegroundWindow",
                return_value=111,
            ),
            mock.patch.object(
                capture.acceptance.win32gui,
                "GetWindowText",
                return_value="Crusader Kings III",
            ),
            mock.patch.object(
                capture.acceptance.win32process,
                "GetWindowThreadProcessId",
                side_effect=lambda hwnd: (10, 999) if hwnd == 111 else (11, 999),
            ),
            mock.patch.object(capture.acceptance, "ACTIVE_CK3_PID", 999),
            mock.patch.object(
                capture.acceptance.win32api,
                "GetKeyboardLayoutList",
                return_value=[0x04090409, 0x08040804],
            ),
            mock.patch.object(
                capture.ctypes,
                "windll",
                SimpleNamespace(user32=already_english_user32),
            ),
        ):
            already_english_gate = capture.force_ck3_english_keyboard_layout(
                layout_artifacts, "already_english"
            )
        assert already_english_gate["result"] == "GREEN"
        assert already_english_gate["before_hkl"] == "0x04090409"
        assert already_english_gate["after_hkl"] == "0x04090409"
        assert already_english_gate["message_posted"] is None
        assert already_english_user32.PostMessageW.calls == []

    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        dll = temporary_root / "bridge.dll"
        injector = temporary_root / "injector.exe"
        dll.write_bytes(b"zg361-title-navigation-dll")
        injector.write_bytes(b"zg361-title-navigation-injector")
        explicit_pipe = (
            capture.NATIVE_TITLE_PIPE_PREFIX + "1" * 32
        )
        native_config = capture.resolve_native_bridge_config(
            dll, injector, explicit_pipe
        )
        assert native_config.mode == "native-headless"
        assert native_config.pipe_name == explicit_pipe
        assert native_config.dll_path == dll.resolve()
        assert native_config.injector_path == injector.resolve()
        bridge_identity = capture.native_bridge_preflight_identity(
            native_config
        )
        assert bridge_identity["dll_sha256"] == capture.isolated.sha256_file(dll)
        assert bridge_identity["injector_sha256"] == (
            capture.isolated.sha256_file(injector)
        )
        assert bridge_identity["visual_fallback"] is False
        generated_pipe_config = capture.resolve_native_bridge_config(
            dll, injector, None
        )
        assert re.fullmatch(
            re.escape(capture.NATIVE_TITLE_PIPE_PREFIX) + r"[0-9a-f]{32}",
            generated_pipe_config.pipe_name,
        )

        for bad_args, expected_error in (
            ((dll, None, explicit_pipe), "must be supplied together"),
            ((dll, injector, r"\\.\pipe\shared"), "run-unique"),
            (
                (
                    temporary_root / "missing.dll",
                    temporary_root / "missing.exe",
                    explicit_pipe,
                ),
                "configuration is invalid",
            ),
        ):
            try:
                capture.resolve_native_bridge_config(*bad_args)
            except capture.acceptance.RunnerError as error:
                assert expected_error in str(error)
            else:
                raise AssertionError(
                    f"invalid native bridge config was accepted: {bad_args!r}"
                )

        hybrid = capture.NativeBridgeLaunchConfig(
            mode="hybrid-fallback",
            pipe_name=explicit_pipe,
            dll_path=dll,
            injector_path=injector,
        )
        with mock.patch.object(
            capture,
            "native_bridge_launch_config_from_environment",
            return_value=hybrid,
        ):
            try:
                capture.resolve_native_bridge_config(
                    None, None, explicit_pipe
                )
            except capture.acceptance.RunnerError as error:
                assert "native-headless" in str(error)
            else:
                raise AssertionError("hybrid fallback bridge was accepted")
        with mock.patch.object(
            capture,
            "native_bridge_launch_config_from_environment",
            side_effect=RuntimeError("bad environment fixture"),
        ):
            try:
                capture.resolve_native_bridge_config(
                    None, None, explicit_pipe
                )
            except capture.acceptance.RunnerError as error:
                assert "native bridge environment is invalid" in str(error)
            else:
                raise AssertionError("bad bridge environment escaped RunnerError")

        binding = {
            "snapshot_id": "native:9",
            "revision": 9,
            "native_revision": 9,
            "date_raw": 777,
            "episode_run_id": "episode-zg361",
            "connection_generation": 4,
        }
        camera = {
            "target_write_blocked": False,
            "settled": True,
            "current_state": [1.0] * 6,
            "target_state": [1.0] * 6,
        }

        def typed_row(
            title_key: str, payload_hash: str
        ) -> dict[str, object]:
            return {
                "ok": True,
                "title_key": title_key,
                "typed_service_payload": {
                    "status": "already_centered",
                    "camera_center": dict(camera),
                },
                "typed_service_payload_sha256": payload_hash,
                "camera_transition": {
                    "before": dict(camera),
                    "after": dict(camera),
                },
            }

        known = typed_row(
            capture.title_navigation_live.DISPLACEMENT_TITLE_KEY, "A" * 64
        )
        integrity = typed_row(
            capture.title_navigation_live.BARONY_TITLE_KEY, "B" * 64
        )
        final = typed_row(
            capture.title_navigation_live.COUNTY_TITLE_KEY, "C" * 64
        )
        shared_sequence = {
            "ok": True,
            "session_binding": binding,
            "known_steps": [known],
            "unknown_step": {
                "ok": True,
                "title_key": capture.title_navigation_live.UNKNOWN_TITLE_KEY,
                "typed_error_sha256": "D" * 64,
                "integrity_probe": integrity,
            },
            "checks": {"shared_contract": True},
        }
        capabilities = {
            "diagnostics": {
                "connected": True,
                "bridge_pid": 4321,
                "connection_generation": 4,
            }
        }

        class MatrixService:
            def capabilities(self) -> dict[str, object]:
                return capabilities

        service = MatrixService()

        def forbidden_fallback(*_args: object, **_kwargs: object) -> None:
            raise AssertionError("visual/input fallback was invoked")

        matrix_artifacts = temporary_root / "matrix"
        matrix_artifacts.mkdir()
        with (
            mock.patch.object(
                capture,
                "native_title_navigation_readiness",
                return_value={"ok": True, "binding": binding},
            ) as readiness,
            mock.patch.object(
                capture.title_navigation_live,
                "_exact_binary_proof",
                return_value={"ok": True, "checks": {"fixture": True}},
            ),
            mock.patch.object(
                capture.title_navigation_live,
                "_run_navigation_sequence",
                return_value=shared_sequence,
            ) as shared_matrix,
            mock.patch.object(
                capture.title_navigation_live,
                "_known_call",
                return_value=final,
            ) as final_call,
            mock.patch.object(
                capture.acceptance,
                "find_ocr_text",
                side_effect=forbidden_fallback,
            ) as find_ocr,
            mock.patch.object(
                capture.acceptance,
                "wait_for_ocr_text",
                side_effect=forbidden_fallback,
            ) as wait_ocr,
            mock.patch.object(
                capture.acceptance,
                "ocr_results",
                side_effect=forbidden_fallback,
            ) as ocr_results,
            mock.patch.object(
                capture.acceptance,
                "deliberate_click",
                side_effect=forbidden_fallback,
            ) as click,
            mock.patch.object(
                capture.acceptance,
                "focus_ck3",
                side_effect=forbidden_fallback,
            ) as focus,
            mock.patch.object(
                capture.acceptance.ImageGrab,
                "grab",
                side_effect=forbidden_fallback,
            ) as grab,
            mock.patch.object(
                capture,
                "force_ck3_english_keyboard_layout",
                side_effect=forbidden_fallback,
            ) as force_layout,
            mock.patch.object(
                capture.acceptance.pyautogui,
                "press",
                side_effect=forbidden_fallback,
            ) as press,
            mock.patch.object(
                capture.acceptance.pyautogui,
                "hotkey",
                side_effect=forbidden_fallback,
            ) as hotkey,
            mock.patch.object(
                capture.acceptance.pyautogui,
                "moveTo",
                side_effect=forbidden_fallback,
            ) as move,
            mock.patch.object(
                capture.acceptance.pyautogui,
                "click",
                side_effect=forbidden_fallback,
            ) as raw_click,
            mock.patch.object(
                capture.acceptance.pyautogui,
                "mouseDown",
                side_effect=forbidden_fallback,
            ) as mouse_down,
            mock.patch.object(
                capture.acceptance.pyautogui,
                "mouseUp",
                side_effect=forbidden_fallback,
            ) as mouse_up,
        ):
            matrix = capture.run_native_title_navigation_matrix(
                service,
                matrix_artifacts,
                tracked_ck3_pid=4321,
                native_bridge=native_config,
                preflight_bridge_identity=bridge_identity,
            )

        assert matrix["result"] == "GREEN"
        assert matrix["mcp_tool"] == "ck3_center_map_on_landed_title_v1"
        assert matrix["tracked_full_acceptance_pid"] == 4321
        assert matrix["successful_typed_call_count"] == 3
        assert matrix["successful_target_write_blocked_values"] == [
            False,
            False,
            False,
        ]
        assert matrix["interaction_audit"]["all_zero"] is True
        assert matrix["interaction_audit"]["fallbacks_enabled"] is False
        assert all(
            value == 0
            for value in matrix["interaction_audit"]["counters"].values()
        )
        assert matrix["inhibit_positive"]["status"] == "skipped"
        assert matrix["inhibit_positive"]["executed"] is False
        assert matrix["inhibit_positive"]["live_claim"] is False
        assert matrix["ffmpeg_started"] is False
        assert re.fullmatch(
            r"[0-9A-F]{64}", matrix["typed_matrix_payload_sha256"]
        )
        persisted = json.loads(
            (
                matrix_artifacts / "05_title_navigation_mcp_matrix.json"
            ).read_text(encoding="utf-8")
        )
        assert persisted == matrix
        readiness.assert_called_once_with(service, tracked_ck3_pid=4321)
        shared_matrix.assert_called_once_with(service)
        assert final_call.call_args.kwargs["title_key"] == "c_bianzhou"
        assert final_call.call_args.kwargs["allowed_statuses"] == {
            "centered",
            "already_centered",
        }
        for forbidden_mock in (
            find_ocr,
            wait_ocr,
            ocr_results,
            click,
            focus,
            grab,
            force_layout,
            press,
            hotkey,
            move,
            raw_click,
            mouse_down,
            mouse_up,
        ):
            forbidden_mock.assert_not_called()

        launch_artifacts = temporary_root / "launch-wiring"
        steam_root = temporary_root / "steam"
        steam_root.mkdir()
        runtime_identity = {"native_bridge_runtime": bridge_identity}
        with (
            mock.patch.object(
                capture, "preflight", return_value=runtime_identity
            ) as preflight,
            mock.patch.object(
                capture.terminal,
                "steam_userdata_root",
                return_value=steam_root,
            ),
            mock.patch.object(
                capture.isolated,
                "steam_workshop_app_roots",
                return_value=[],
            ),
            mock.patch.object(
                capture.isolated, "registered_workshop_targets"
            ),
            mock.patch.object(capture.isolated, "ensure_test_paths_safe"),
            mock.patch.object(
                capture.isolated, "protected_snapshot", return_value={}
            ),
            mock.patch.object(capture.isolated, "verify_protected_storage"),
            mock.patch.object(capture, "write_evidence_index"),
            mock.patch.object(
                capture,
                "run_cell",
                return_value={"result": "GREEN", "error_reason": None},
            ) as run_cell,
        ):
            assert (
                capture.main(
                    artifacts_dir=str(launch_artifacts),
                    keep_userdir=True,
                    bridge_dll=str(dll),
                    bridge_injector=str(injector),
                    bridge_pipe=explicit_pipe,
                )
                == 0
            )
        selected = preflight.call_args.kwargs["native_bridge"]
        assert selected == native_config
        expected_state = launch_artifacts.with_name(
            launch_artifacts.name + "_native_state"
        )
        expected_profile = expected_state / "profile"
        assert run_cell.call_args.args == (
            launch_artifacts / "cell",
            expected_profile,
            True,
        )
        assert run_cell.call_args.kwargs["state_dir"] == expected_state
        assert run_cell.call_args.kwargs["native_bridge"] == native_config

    camera_probe_cell = inspect.getsource(capture.run_cell)
    for token in (
        "if promo_camera_probe:",
        '"05_title_navigation_probe_preflight"',
        "force_ck3_english_keyboard_layout(artifacts)",
        "run_native_title_navigation_matrix(",
        '"probe_only": True',
        '"ffmpeg_started": False',
        'result == "GREEN" and not promo_camera_probe',
        "spec = make_spec(state_dir, acceptance.CK3_EXE.parent.parent)",
        "spec.profile_dir.resolve() != userdir",
        "exclusive_launch_lock(spec.game_exe)",
        'exclusive_state_lock(spec.state_dir, "zhongguo-361-acceptance")',
        "NativeHeadlessGameplayDriver(",
        "native_bridge.pipe_name",
        "command_timeout_seconds=NATIVE_TITLE_COMMAND_TIMEOUT_S",
        "launch_native_ck3(",
        "native_bridge=native_bridge",
        "verify_prepared_profile=False",
        "stop_tracked(",
        '"native_launch_sequence": "suspended_inject_resume"',
    ):
        assert token in camera_probe_cell, token
    for retired in (
        "acceptance.launch_ck3_process",
        "acceptance.start_process_watchdog",
        "acceptance.stop_ck3_process",
        "recenter_promo_camera_on_player_capital",
    ):
        assert retired not in camera_probe_cell, retired
    try:
        capture.main(
            preflight_only=True,
            promo_capture=True,
            promo_camera_probe=True,
        )
    except capture.acceptance.RunnerError as error:
        assert "mutually exclusive" in str(error)
    else:
        raise AssertionError("conflicting promo modes were accepted")

    shared_open_drawer = inspect.getsource(capture.isolated.ensure_decisions_panel)
    for token in (
        'acceptance.pyautogui.press("f8")',
        'f"{stem}_f8_no_panel.png"',
        "native_right_rail_scan_points",
        "is_decisions_shortcut_tooltip",
        "dynamically located native Decisions HUD tab",
        'f"{stem}_decisions_panel_scan.png"',
    ):
        assert token in shared_open_drawer, token
    assert "0.987" not in shared_open_drawer
    assert "0.367" not in shared_open_drawer
    assert shared_open_drawer.index('acceptance.pyautogui.press("f8")') < (
        shared_open_drawer.index("native_right_rail_scan_points")
    )
    shared_header_wait = inspect.getsource(
        capture.isolated._wait_for_decisions_header
    )
    assert "stable_hits >= 2" in shared_header_wait
    assert "raise" not in shared_header_wait

    scan_points = capture.isolated.native_right_rail_scan_points(2560, 1440)
    assert scan_points[0] == (int(2560 * 0.987), int(1440 * 0.055))
    assert scan_points[-1][1] <= int(1440 * 0.78)
    assert scan_points[-1][1] >= int(1440 * 0.78) - 31
    assert all(point[0] == int(2560 * 0.987) for point in scan_points)
    assert max(
        right[1] - left[1] for left, right in zip(scan_points, scan_points[1:])
    ) <= 31
    robert_decisions_tooltip = [
        {"text": "决议", "center": [2443, 552]},
        {"text": "F8", "center": [2463, 581]},
    ]
    hover = (int(2560 * 0.987), int(1440 * 0.367))
    assert capture.isolated.is_decisions_shortcut_tooltip(
        robert_decisions_tooltip, hover, 2560, 1440
    )
    assert not capture.isolated.is_decisions_shortcut_tooltip(
        [
            {"text": "派系", "center": [2443, 552]},
            {"text": "F7", "center": [2463, 581]},
        ],
        hover,
        2560,
        1440,
    )
    assert not capture.isolated.is_decisions_shortcut_tooltip(
        robert_decisions_tooltip, (hover[0], hover[1] + 300), 2560, 1440
    )

    assert capture.EXPECTED_PLAYER_HISTORY_ID == "han_8052"
    for late_marker in capture.REQUIRED_LATE_FIXTURE_MARKERS:
        assert late_marker not in capture.REQUIRED_FIXTURE_MARKERS
    assert capture.HISTORICAL_TARGET_PASS_MARKER in (
        capture.REQUIRED_LATE_FIXTURE_MARKERS
    )
    newcomer_product_marker = (
        "ZG361: newcomer enters first review with 3.25 protection"
    )
    assert newcomer_product_marker not in capture.REQUIRED_PRODUCT_MARKERS
    assert capture.REQUIRED_LATE_PRODUCT_MARKERS[newcomer_product_marker] == 1
    validate_markers = inspect.getsource(capture.MarkerStream.validate)
    assert "if final:" in validate_markers
    assert "required_markers += REQUIRED_LATE_FIXTURE_MARKERS" in validate_markers
    assert "required_product_markers.update(REQUIRED_LATE_PRODUCT_MARKERS)" in validate_markers
    assert len(capture.EXPECTED_REVIEWED_OFFICIAL_HISTORY_IDS) == 18
    assert len(capture.EXPECTED_HISTORICAL_COHORT_HISTORY_IDS) == 21
    assert "han_5253" in capture.EXPECTED_REVIEWED_OFFICIAL_HISTORY_IDS
    assert "han_6875" in capture.EXPECTED_REVIEWED_OFFICIAL_HISTORY_IDS
    assert "han_7247" in capture.EXPECTED_HISTORICAL_COHORT_HISTORY_IDS
    assert "han_7247" not in capture.EXPECTED_REVIEWED_OFFICIAL_HISTORY_IDS
    assert "han_6821" not in capture.EXPECTED_REVIEWED_OFFICIAL_HISTORY_IDS
    assert capture.PROMO_CLEAN_SPANS == (
        "calibration",
        "managed_scoreboard",
        "policy_cockpit",
        "jingcha_mandate",
        "free_jingcha_planner",
        "superior_assigned_325",
        "received_scoreboard_with_325",
        "policy_card_001",
        "policy_card_007",
        "policy_card_020",
        "policy_card_022",
        "policy_card_026",
        "policy_card_361",
    )
    assert capture.PROMO_PERSONAL_RESULT_FIELD_REGION == (0.20, 0.34, 0.42, 0.40)
    provenance = capture.promo_real_character_provenance("han_5253")
    assert [row["history_id"] for row in provenance["subjects"]] == [
        "han_8052",
        "han_5253",
    ]
    assert provenance["subjects"][0]["roles"] == ["manager", "emperor"]
    assert provenance["subjects"][1]["roles"] == [
        "reviewed_official",
        "hunan_governor",
    ]
    assert all(not row["temporary_or_generated"] for row in provenance["subjects"])
    assert all(
        "expected_runtime_contract" in row for row in provenance["subjects"]
    )
    assert provenance["fixture_constructor_counts"] == {
        "create_character": 0,
        "create_title": 0,
        "grant_title": 0,
        "set_father": 0,
        "set_mother": 0,
        "set_spouse": 0,
        "add_relation": 0,
        "set_relation": 0,
    }
    assert provenance["title_history_assertions"] == {
        "h_china_holder_at_start": "han_8052",
        "reviewed_official_title_at_start": "k_hunan",
        "reviewed_official_holder_at_start": "han_5253",
        "reviewed_official_holder_date": "1066.1.1",
        "reviewed_official_title_liege_at_start": "h_china",
        "reviewed_official_direct_liege_holder_at_start": "han_8052",
        "reviewed_official_direct_liege_holder_date": "1063.4.30",
    }
    for history_id in capture.EXPECTED_REVIEWED_OFFICIAL_HISTORY_IDS:
        candidate_provenance = capture.promo_real_character_provenance(history_id)
        assert [
            row["history_id"] for row in candidate_provenance["subjects"]
        ] == ["han_8052", history_id]
    dynamic_provenance = capture.promo_real_character_provenance("han_6875")
    assert [row["history_id"] for row in dynamic_provenance["subjects"]] == [
        "han_8052",
        "han_6875",
    ]
    assert dynamic_provenance["subjects"][1]["display_name"] == "唐介"
    assert dynamic_provenance["subjects"][1]["selection"] == (
        "runtime_lowest_ranked_historical_duke_plus_from_hard_allowlist"
    )
    assert dynamic_provenance["title_history_assertions"][
        "reviewed_official_title_liege_at_start"
    ] == "h_china"
    for rejected_id in ("han_7247", "han_999999999"):
        try:
            capture.promo_real_character_provenance(rejected_id)
        except capture.acceptance.RunnerError as error:
            assert "outside the frozen allowlist" in str(error)
        else:
            raise AssertionError("assessed-only or unknown history id must fail provenance")

    class StaticMarkerStream:
        def __init__(self, lines: list[str]):
            self.lines = lines

        def pump(self) -> None:
            return None

    marker_stream = StaticMarkerStream(
        ["fixture.cpp: ZGA: DATA historical_personal_result_target han_6875"]
    )
    assert (
        capture.resolved_historical_personal_result_target(marker_stream)
        == "han_6875"
    )
    for rejected_lines in (
        ["ZGA: DATA historical_personal_result_target han_7247"],
        ["ZGA: DATA historical_personal_result_target han_999999999"],
        [
            "ZGA: DATA historical_personal_result_target han_6875",
            "ZGA: DATA historical_personal_result_target han_5253",
        ],
    ):
        try:
            capture.resolved_historical_personal_result_target(
                StaticMarkerStream(rejected_lines)
            )
        except capture.acceptance.RunnerError:
            pass
        else:
            raise AssertionError("invalid or ambiguous historical marker must fail")
    assert capture.fixture_source_errors() == []
    assert "test_zg361_clean_promo_fixture.py" in inspect.getsource(capture.preflight)

    clean_frame = inspect.getsource(capture.assert_promo_frame_clean)
    assert "drawer_absence_consecutive_samples" in clean_frame
    assert "_promo_decisions_header_hits" in clean_frame
    assert "promo_product_event_overlay_evidence" in clean_frame
    assert '"product_event_overlay": product_event_overlay' in clean_frame
    assert 'for token in ("决议", "Decisions")' in inspect.getsource(
        capture._promo_decisions_header_hits
    )

    assert capture.SCOREBOARD_BUTTON_REGION == (0.86, 0.05, 0.985, 0.16)
    assert capture.DECISIONS_CLOSE_BUTTON == (0.961, 0.064)
    close_x, close_y = capture.DECISIONS_CLOSE_BUTTON
    assert round(close_x * 2560) == 2460
    assert round(close_y * 1440) == 92
    assert capture.SCOREBOARD_TITLE_CLOSE_BUTTON == (0.778, 0.167)
    panel_close_x, panel_close_y = capture.SCOREBOARD_TITLE_CLOSE_BUTTON
    assert int(panel_close_x * 2560) == 1991
    assert int(panel_close_y * 1440) == 240
    assert capture.SCOREBOARD_BACKDROP_POINT == (0.050, 0.500)
    assert capture.CHARACTER_WINDOW_CLOSE_BUTTON == (0.2891, 0.0181)
    character_close_x, character_close_y = capture.CHARACTER_WINDOW_CLOSE_BUTTON
    assert int(character_close_x * 2560) == 740
    assert int(character_close_y * 1440) == 26
    assert capture.SCOREBOARD_GENERATED_ROW_LINKS == 160
    left, top, right, bottom = capture.SCOREBOARD_BUTTON_REGION
    assert left <= 0.924 <= right and top <= 0.101 <= bottom
    assert not (left <= 0.846 <= right and top <= 0.173 <= bottom)

    validator = inspect.getsource(capture.MarkerStream.validate)
    assert re.search(
        r"if final:\s+self\.validate_small_cohort_probe\(\)", validator
    )
    small_probe = object.__new__(capture.MarkerStream)
    small_probe.lines = []
    try:
        small_probe.validate_small_cohort_probe()
    except capture.acceptance.RunnerError as error:
        assert "either scheduled or explicitly unavailable" in str(error)
    else:
        raise AssertionError("missing late small-cohort marker must fail")
    small_probe.lines = [
        "ZGA: TEST INFO ai_small_cohort_candidate_unavailable"
    ]
    small_probe.validate_small_cohort_probe()
    small_probe.lines = [
        "ZGA: TEST INFO ai_small_cohort_review_scheduled",
        "ZGA: TEST PASS ai_small_cohort_neutral_settlement",
        "ZGA: TEST PASS ai_small_cohort_same_year_idempotent",
    ]
    small_probe.validate_small_cohort_probe()

    # A clean score row and the cockpit itself occupy the same classic x/y
    # lanes as event text/options. Neither may be treated as dismissible UI.
    clean_board = [
        {"center": [1280, 243], "bbox": [1178, 228, 1382, 258]},
        {"center": [908, 1062], "bbox": [805, 1049, 1012, 1075]},
    ]
    assert not capture.promo_event_modal_evidence(clean_board, 2560, 1440)
    clean_cockpit = clean_board + [
        {"center": [1282, 409], "bbox": [1129, 398, 1435, 421]},
        {"center": [1280, 536], "bbox": [732, 525, 1828, 548]},
    ]
    assert not capture.promo_event_modal_evidence(clean_cockpit, 2560, 1440)
    native_event = clean_board + [
        {
            "text": "京察之期",
            "center": [720, 318],
            "bbox": [575, 301, 865, 335],
        },
        {"center": [904, 470], "bbox": [624, 459, 1184, 482]},
    ]
    assert capture.promo_event_modal_evidence(native_event, 2560, 1440)
    assert capture.promo_event_title_evidence(
        native_event, 2560, 1440, "京察之期"
    )
    pause_reason_only = [
        {
            "text": "野狗与小白兔",
            "center": [828, 401],
            "bbox": [700, 385, 956, 417],
        },
        {
            "text": "因京察之期事件暂停",
            "center": [2109, 1354],
            "bbox": [2000, 1340, 2218, 1368],
        },
    ]
    assert not capture.promo_event_title_evidence(
        pause_reason_only, 2560, 1440, "京察之期"
    )
    known_product_event = [
        {
            "text": "野狗与小白兔",
            "center": [828, 401],
            "bbox": [700, 385, 956, 417],
        },
        {
            "text": "宽严相济：野狗留用观察，小白兔好言安抚。",
            "center": [930, 989],
            "bbox": [700, 975, 1160, 1003],
        },
        {
            "text": "严惩野狗、劝退小白兔。",
            "center": [930, 1043],
            "bbox": [700, 1029, 1160, 1057],
        },
    ]
    preferred_title, preferred_option = (
        capture.promo_preferred_product_event_option(
            known_product_event, 2560, 1440
        )
    )
    assert preferred_title == "野狗与小白兔"
    assert preferred_option is not None
    assert preferred_option["text"].startswith("宽严相济")
    assert capture.promo_product_event_overlay_evidence(
        "free_jingcha_planner", native_event, 2560, 1440
    )
    assert not capture.promo_product_event_overlay_evidence(
        "free_jingcha_planner", clean_board, 2560, 1440
    )
    assert not capture.promo_product_event_overlay_evidence(
        "managed_scoreboard", native_event, 2560, 1440
    )

    representative_rows = native_event + [
        {
            "text": "河北经略使，显宗恪",
            "center": [909, 508],
            "bbox": [805, 495, 1013, 521],
        },
        {
            "text": "山南观察使，曾公亮",
            "center": [907, 600],
            "bbox": [803, 587, 1012, 613],
        },
    ]
    representative = capture.select_representative_scoreboard_row(
        representative_rows, 2560, 1440
    )
    assert representative is not None
    row, personal_name = representative
    assert row["text"] == "河北经略使，显宗恪"
    assert personal_name == "显宗恪"

    scoreboard_gui = bom_text(SCOREBOARD_GUI)
    row_click = 'onclick = "[DefaultOnCharacterClick(Character.GetID)]"'
    assert scoreboard_gui.count(row_click) == 160
    assert len(re.findall(r"zg361_sb_m_\d{2}_char", scoreboard_gui)) == 80
    assert len(re.findall(r"zg361_sb_r_\d{2}_char", scoreboard_gui)) == 80

    policies = re.search(
        r"def capture_policy_cards\(.*?(?=^def )", runner, re.M | re.S
    )
    assert policies is not None
    policy_body = policies.group(0)
    assert "settle_promo_interruptions" in policy_body
    assert "stop_event_title=event_title" in policy_body
    assert "PROMO_EVENT_TITLE_REGION" in policy_body
    assert "acceptance.ensure_game_paused" in policy_body
    assert "open_decision_detail" not in policy_body
    assert "clean_policy_{mechanism_id:03d}_dispatched" in policy_body
    assert "recorder.clean_hold" in policy_body
    assert "clean_policy_chain_completed" in policy_body
    for token in (
        "timeline_service: GameplayBridgeService",
        "arm_native_speed_one(timeline_service)",
        "pause_after_promo_event_click",
        'stem=f"{stem}_close"',
        '"premature_successor_marker_count"',
        'stream.count(successor_marker)',
        'pause_evidence["result"] = "RED"',
        '"policy successor dispatched before predecessor capture"',
    ):
        assert token in policy_body, token
    policy_click = (
        'acceptance.deliberate_click(option, f"close policy card '
        '{mechanism_id:03d}")'
    )
    assert policy_body.index("arm_native_speed_one(timeline_service)") < (
        policy_body.index(policy_click)
    )
    assert policy_body.index(policy_click) < policy_body.index(
        "pause_after_promo_event_click"
    )
    assert (
        'acceptance.deliberate_click(option, f"close policy card '
        '{mechanism_id:03d}")\n'
        "        pause_evidence = pause_after_promo_event_click("
    ) in policy_body
    assert 'acceptance.ensure_game_paused(artifacts, f"{stem}_closed")' not in (
        policy_body
    )
    assert body.index("capture_received_scoreboard(") < body.index(
        "capture_policy_cards("
    )
    assert body.count("timeline_service=title_navigation_service") >= 3

    jingcha = re.search(
        r"def capture_jingcha_planner\(.*?(?=^def )", runner, re.M | re.S
    )
    assert jingcha is not None
    jingcha_body = jingcha.group(0)
    assert "open_decision_detail" not in jingcha_body
    assert "clean_jingcha_dispatch_scheduled" in jingcha_body
    assert "clean_jingcha_dispatched" in jingcha_body
    assert "acceptance.read_hud_game_date" in jingcha_body
    assert 'stop_event_title="京察之期"' in jingcha_body
    assert "PROMO_EVENT_TITLE_REGION" in jingcha_body
    assert "pause_after_jingcha_host_click" in jingcha_body
    assert 'pause_service.execute_step("set-speed-1")' in jingcha_body
    assert jingcha_body.index(
        'pause_service.execute_step("set-speed-1")'
    ) < jingcha_body.index(
        'acceptance.deliberate_click(host_option, "production host Jingcha option")'
    )
    assert jingcha_body.index(
        'acceptance.deliberate_click(host_option, "production host Jingcha option")'
    ) < jingcha_body.index("pause_after_jingcha_host_click")
    assert jingcha_body.index("pause_after_jingcha_host_click") < jingcha_body.index(
        "plan_button = acceptance.wait_for_ocr_text"
    )
    assert jingcha_body.index(
        "plan_button = acceptance.wait_for_ocr_text"
    ) < jingcha_body.index(
        'acceptance.deliberate_click(plan_button, "production plan Jingcha activity button")'
    )

    host_pause = inspect.getsource(capture.pause_after_jingcha_host_click)
    for token in (
        'service.execute_step("pause-map")',
        "service.snapshot()",
        "acceptance.read_hud_game_date",
        "native_pause_observations",
        "played_character_stable",
        "stream.pump()",
        "PERSONAL_SWITCH_SCHEDULED_MARKER",
        "paused_day >= due_day",
        '"date_before_due": paused_day < due_day',
        '"pause_completed_before_personal_switch_due": paused_day < due_day',
        '"paused_within_two_days": 0 <= pause_delta_days <= 2',
        '"last_three_dates_identical": frozen',
        '"pause_method": "native_mcp_pause_map"',
        '"09_jingcha_host_immediate_pause_gate.json"',
    ):
        assert token in host_pause, token
    assert "acceptance.ensure_game_paused" not in host_pause
    assert "pyautogui" not in host_pause
    assert capture.JINGCHA_PERSONAL_SWITCH_DELAY_DAYS == 90

    interruption = inspect.getsource(capture.settle_promo_interruptions)
    assert "stop_event_title: str | None = None" in interruption
    assert "promo_event_title_evidence" in interruption
    assert interruption.index("promo_event_title_evidence") < interruption.index(
        "acceptance.select_stall_recovery"
    )
    assert "promo_preferred_product_event_option" in interruption
    assert "blocked_known_event_safe_option_missing" in interruption
    assert "PROMO_PROTECTED_EVENT_TITLES" in interruption
    assert "blocked_protected_target_event" in interruption
    assert "ensure_hud_date_frozen" in interruption
    assert "acceptance.ensure_game_paused" not in interruption

    pause_by_date = inspect.getsource(capture.ensure_hud_date_frozen)
    for token in (
        "acceptance.read_hud_game_date",
        "len(set(observations[-3:])) == 1",
        "timeline pause by HUD date",
        '"last_three_dates_identical": frozen',
        'f"{stem}_date_freeze_gate.json"',
    ):
        assert token in pause_by_date, token

    class FakeImage:
        def save(self, path: Path) -> None:
            Path(path).write_bytes(b"fake image")

    moving_then_frozen = iter((100, 101, 102, 103, 103, 103, 103, 103))
    with tempfile.TemporaryDirectory() as temporary:
        artifacts = Path(temporary)
        with (
            mock.patch.object(capture.acceptance, "focus_ck3"),
            mock.patch.object(
                capture.acceptance.ImageGrab,
                "grab",
                side_effect=[FakeImage() for _ in range(8)],
            ),
            mock.patch.object(
                capture.acceptance,
                "read_hud_game_date",
                side_effect=lambda _image: (next(moving_then_frozen), (0, 0)),
            ),
            mock.patch.object(
                capture.acceptance.pyautogui, "size", return_value=(2560, 1440)
            ),
            mock.patch.object(capture.acceptance, "deliberate_click") as click,
            mock.patch.object(capture.time, "sleep"),
        ):
            frozen = capture.ensure_hud_date_frozen(
                artifacts, "mock_chain", probe_interval_s=0.0
            )
        click.assert_called_once()
        assert frozen["result"] == "GREEN"
        assert frozen["pause_method"] == "timeline_click"
        assert frozen["date_observations"] == [100, 101, 102, 103, 103, 103, 103, 103]
        assert (artifacts / "mock_chain_date_freeze_gate.json").is_file()

    class NoPersonalSwitchStream:
        def pump(self) -> None:
            return None

        def count(self, marker: str) -> int:
            assert marker == capture.PERSONAL_SWITCH_SCHEDULED_MARKER
            return 0

    class NativePauseService:
        def __init__(self) -> None:
            self.steps: list[str] = []
            self.snapshots = iter(
                (
                    {"revision": 2, "native_revision": 2, "date_raw": 24000, "paused": True, "active_event": {"instance_id": 77}, "played_character": {"character_id": 901, "alive": True}},
                    {"revision": 3, "native_revision": 3, "date_raw": 24024, "paused": False, "active_event": None, "played_character": {"character_id": 901, "alive": True}},
                    {"revision": 4, "native_revision": 4, "date_raw": 24024, "paused": False, "active_event": None, "played_character": {"character_id": 901, "alive": True}},
                    {"revision": 5, "native_revision": 5, "date_raw": 24024, "paused": True, "active_event": None, "played_character": {"character_id": 901, "alive": True}},
                    {"revision": 5, "native_revision": 5, "date_raw": 24024, "paused": True, "active_event": None, "played_character": {"character_id": 901, "alive": True}},
                    {"revision": 5, "native_revision": 5, "date_raw": 24024, "paused": True, "active_event": None, "played_character": {"character_id": 901, "alive": True}},
                )
            )

        def snapshot(self) -> dict[str, object]:
            return next(self.snapshots)

        def execute_step(self, step: str) -> dict[str, object]:
            self.steps.append(step)
            return {"accepted": True, "step": step, "backend_id": "native-headless"}

    pause_service = NativePauseService()
    pre_click_snapshot = {
        "revision": 1,
        "native_revision": 1,
        "date_raw": 24000,
        "paused": True,
        "active_event": {"instance_id": 77},
        "played_character": {"character_id": 901, "alive": True},
    }
    with tempfile.TemporaryDirectory() as temporary:
        artifacts = Path(temporary)
        with (
            mock.patch.object(
                capture.acceptance.ImageGrab,
                "grab",
                return_value=FakeImage(),
            ),
            mock.patch.object(
                capture.acceptance,
                "read_hud_game_date",
                return_value=(1001, (0, 0)),
            ),
            mock.patch.object(capture.time, "sleep"),
        ):
            pause_gate = capture.pause_after_jingcha_host_click(
                pause_service,
                NoPersonalSwitchStream(),
                artifacts,
                mandate_day=1000,
                pre_click_snapshot=pre_click_snapshot,
            )
        assert pause_service.steps == ["pause-map"]
        assert pause_gate["result"] == "GREEN"
        assert pause_gate["personal_switch_due_day_ordinal"] == 1090
        assert pause_gate["paused_day_ordinal"] == 1001
        assert pause_gate["pause_delta_days"] == 1
        assert pause_gate["paused_within_two_days"] is True
        assert pause_gate["pause_completed_before_personal_switch_due"] is True
        assert pause_gate["personal_switch_marker_count"] == 0
        assert pause_gate["played_character_stable"] is True
        assert pause_gate["pause_method"] == "native_mcp_pause_map"
        assert (artifacts / "09_jingcha_host_immediate_pause_gate.json").is_file()

    def event_item(
        text: str, center: tuple[int, int], width: int = 500
    ) -> dict[str, object]:
        x, y = center
        return {
            "text": text,
            "center": [x, y],
            "bbox": [x - width // 2, y - 12, x + width // 2, y + 12],
            "score": 0.99,
        }

    def event_frame(
        title: str, options: tuple[tuple[str, tuple[int, int]], ...]
    ) -> list[dict[str, object]]:
        return [
            event_item(title, (720, 318), 440),
            event_item("这是一段足够宽的正式事件叙事正文。", (850, 560), 900),
            *(event_item(text, center, 620) for text, center in options),
        ]

    class FakeDesktopImage(FakeImage):
        size = (2560, 1440)

        def __init__(self, items: list[dict[str, object]]) -> None:
            self.items = items

    class FakeDesktop:
        def __init__(self) -> None:
            self.state = 0
            self.clicks: list[tuple[int, int]] = []
            self.frames = (
                event_frame("例行朝议", (("知道了", (930, 1000)),)),
                event_frame(
                    "野狗与小白兔",
                    (
                        ("宽严相济：野狗留用观察，小白兔好言安抚。", (930, 989)),
                        ("严惩野狗、劝退小白兔", (930, 1043)),
                    ),
                ),
                event_frame("京察之期", (("依例举办京察", (930, 989)),)),
            )

        def grab(self) -> FakeDesktopImage:
            return FakeDesktopImage(
                [dict(item) for item in self.frames[self.state]]
            )

        def click(self, point: tuple[int, int], _label: str) -> None:
            expected = ((930, 1000), (930, 989))[self.state]
            assert point == expected, (point, expected)
            self.clicks.append(point)
            self.state += 1

    desktop = FakeDesktop()
    selected_states: list[int] = []
    real_select = capture.acceptance.select_stall_recovery

    def select_with_state(items, image, allow_succession=False):
        selected_states.append(desktop.state)
        return real_select(items, image, allow_succession=allow_succession)

    def write_fake_bundle(image, items, artifacts, stem):
        image.save(artifacts / f"{stem}.png")
        return 0.0

    with tempfile.TemporaryDirectory() as temporary:
        artifacts = Path(temporary)
        with (
            mock.patch.object(capture.acceptance, "focus_ck3"),
            mock.patch.object(capture.acceptance.ImageGrab, "grab", desktop.grab),
            mock.patch.object(
                capture.acceptance,
                "ocr_box_results",
                side_effect=lambda image, _region: [
                    dict(item) for item in image.items
                ],
            ),
            mock.patch.object(
                capture.acceptance,
                "read_hud_game_date",
                side_effect=lambda _image: (2000 + desktop.state, (0, 0)),
            ),
            mock.patch.object(
                capture.acceptance,
                "select_stall_recovery",
                side_effect=select_with_state,
            ),
            mock.patch.object(
                capture.acceptance,
                "write_recovery_bundle",
                side_effect=write_fake_bundle,
            ),
            mock.patch.object(
                capture.acceptance, "deliberate_click", side_effect=desktop.click
            ),
            mock.patch.object(capture.time, "sleep"),
        ):
            dismissed = capture.settle_promo_interruptions(
                artifacts,
                "mock_chain",
                observation_s=0.0,
                stop_event_title="京察之期",
            )
            assert [row["selected_text"] for row in dismissed] == [
                "知道了",
                "宽严相济：野狗留用观察，小白兔好言安抚。",
            ]
            assert desktop.clicks == [(930, 1000), (930, 989)]
            assert selected_states == [0, 1]
            assert (artifacts / "mock_chain_target_event_visible.png").is_file()
            for ordinal, expected_day in ((1, 2001), (2, 2002)):
                gate = json.loads(
                    (
                        artifacts
                        / f"mock_chain_interruption_{ordinal:02d}_dismissed_date_freeze_gate.json"
                    ).read_text(encoding="utf-8")
                )
                assert gate["result"] == "GREEN"
                assert gate["pause_method"] == "already_frozen"
                assert gate["date_observations"] == [expected_day] * 4

            clicks_before_wrong_step = len(desktop.clicks)
            try:
                capture.settle_promo_interruptions(
                    artifacts,
                    "mock_wrong_step",
                    observation_s=0.0,
                    stop_event_title="上司考定",
                )
            except capture.acceptance.RunnerError as exc:
                assert "protected promo target surfaced" in str(exc)
                assert "京察之期" in str(exc)
            else:
                raise AssertionError("wrong-step Jingcha target was not blocked")
            assert len(desktop.clicks) == clicks_before_wrong_step
            blocked = json.loads(
                (
                    artifacts
                    / "mock_wrong_step_protected_target_event_decision.json"
                ).read_text(encoding="utf-8")
            )
            assert blocked["status"] == "blocked_protected_target_event"
            assert blocked["recovery_kind"] == "京察之期"
            assert blocked["selected_text"] is None

    jingcha_advance = inspect.getsource(capture.advance_to_jingcha_mandate)
    for token in (
        "timeout_s: float = 60.0",
        'stop_event_title="京察之期"',
        "settle_promo_interruptions",
        "stream.pump()",
        "zg361_clean_jingcha_resume_",
    ):
        assert token in jingcha_advance, token

    personal = re.search(
        r"def capture_superior_assigned_result\(.*?(?=^def )", runner, re.M | re.S
    )
    assert personal is not None
    personal_body = personal.group(0)
    assert "advance_to_personal_switch" in personal_body
    assert "resolved_historical_personal_result_target" in personal_body
    assert "HISTORICAL_TARGET_DATA_MARKER_PREFIX" in personal_body
    assert "HISTORICAL_TARGET_PASS_MARKER" in personal_body
    assert "recorder.resolve_reviewed_subject" in personal_body
    assert "personal_result_target_projected_bottom_two" in personal_body
    assert "clean_policy_chain_scheduled" in personal_body
    assert "PROMO_PERSONAL_RESULT_FIELD_REGION" in personal_body
    assert '("你的绩效", "3.25")' in personal_body
    assert '("3.75", "3.5", "zg361_"' in personal_body
    assert "personal result must render exactly one grade" not in personal_body
    assert "grades = tuple" not in personal_body

    switch_advance = inspect.getsource(capture.advance_to_personal_switch)
    for token in (
        "timeout_s: float = PERSONAL_SWITCH_WAIT_TIMEOUT_S",
        "PERSONAL_SWITCH_SCHEDULED_MARKER",
        "settle_promo_interruptions",
        'stop_event_title="上司考定"',
        "resume_personal_switch_timeline_native",
        '"silent_pause"',
        '"10_personal_switch_timeline_gate.json"',
        'active_event_id is None',
        "time.monotonic() + timeout_s",
    ):
        assert token in switch_advance, token
    assert capture.PERSONAL_SWITCH_WAIT_TIMEOUT_S == 240.0

    class NativeTimelineService:
        def __init__(self) -> None:
            self.speed = 1
            self.paused = True
            self.date_raw = 100
            self.steps: list[str] = []

        def snapshot(self) -> dict[str, object]:
            if not self.paused:
                self.date_raw += 1
            return {
                "revision": len(self.steps) + self.date_raw,
                "native_revision": len(self.steps) + self.date_raw,
                "date_raw": self.date_raw,
                "paused": self.paused,
                "speed": self.speed,
                "active_event": None,
            }

        def execute_step(self, step: str) -> dict[str, object]:
            self.steps.append(step)
            if step == "set-speed-5":
                self.speed = 5
            elif step == "resume-map":
                self.paused = False
            else:
                raise AssertionError(step)
            return {"step": step, "accepted": True}

    timeline_service = NativeTimelineService()
    native_resume = capture.resume_personal_switch_timeline_native(
        timeline_service, reason="silent_pause", timeout_s=1.0
    )
    assert timeline_service.steps == ["set-speed-5", "resume-map"]
    assert native_resume["result"] == "GREEN"
    assert native_resume["reason"] == "silent_pause"
    assert native_resume["resumed_date_raw"] > native_resume["starting_date_raw"]

    class PersonalSwitchStream:
        marker_ready = False

        def pump(self) -> None:
            return None

        def count(self, marker: str) -> int:
            assert marker == capture.PERSONAL_SWITCH_SCHEDULED_MARKER
            return int(self.marker_ready)

    personal_stream = PersonalSwitchStream()
    resume_reasons: list[str] = []

    def fake_native_resume(_service, *, reason, timeout_s=10.0):
        del timeout_s
        resume_reasons.append(reason)
        if reason == "silent_pause":
            personal_stream.marker_ready = True
        return {"reason": reason, "result": "GREEN"}

    paused_snapshot = {
        "revision": 1,
        "native_revision": 1,
        "date_raw": 100,
        "paused": True,
        "speed": 5,
        "active_event": None,
    }
    fake_service = SimpleNamespace(snapshot=lambda: paused_snapshot)
    with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
        capture,
        "resume_personal_switch_timeline_native",
        side_effect=fake_native_resume,
    ), mock.patch.object(
        capture,
        "settle_promo_interruptions",
        return_value=[],
    ), mock.patch.object(capture.time, "monotonic", return_value=0.0):
        recovered = capture.advance_to_personal_switch(
            personal_stream,
            Path(temp_dir),
            timeline_service=fake_service,
            due_day_ordinal=190,
            timeout_s=1.0,
        )
        assert recovered == []
        assert resume_reasons == ["initial_post_jingcha_resume", "silent_pause"]
        gate = json.loads(
            (Path(temp_dir) / "10_personal_switch_timeline_gate.json").read_text(
                encoding="utf-8"
            )
        )
        assert gate["result"] == "GREEN"
        assert gate["due_day_ordinal"] == 190
        assert gate["marker_count"] == 1

    decisions = bom_text(FIXTURE / "common" / "decisions" / "zga_decisions.txt")
    found = tuple(
        int(value)
        for value in re.findall(r"^zga_promo_policy_(\d{3})_decision\s*=", decisions, re.M)
    )
    assert found == IDS, found
    for identifier in IDS:
        assert decisions.count(f"trigger_event = zg361m.{identifier}") == 1

    for language in ("english", "simp_chinese"):
        loc = bom_text(
            FIXTURE / "localization" / language / f"zga_l_{language}.yml"
        )
        for identifier in IDS:
            assert f" zga_promo_policy_{identifier:03d}_decision:0 " in loc
            assert f" zga_promo_policy_{identifier:03d}_decision_confirm:0 " in loc
    print("GREEN: ZhongGuo post-loading promo capture contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
