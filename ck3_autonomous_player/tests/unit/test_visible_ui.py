from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.control.executor import (  # noqa: E402
    _MOUSEEVENTF_LEFTDOWN,
    _MOUSEEVENTF_LEFTUP,
    VisibleUiDriver,
    _IssuedControl,
    _prepare_left_click_batch,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.vision.classifier import (  # noqa: E402
    AnchorSpec,
    ControlSpec,
    ScreenSpec,
    UiContract,
    load_ui_contract,
    require_canonical_phase_b_contract,
)
from xar_autoplayer.vision.model import (  # noqa: E402
    Observation,
    OcrSpan,
    StableObservation,
    VisibleAnchor,
    VisibleControl,
)
from xar_autoplayer.vision.ocr import normalize_visible_text, ocr_spans  # noqa: E402
from xar_autoplayer.vision.window import BoundGameWindow  # noqa: E402


UI_CONTRACT = (
    ROOT / "configs" / "ui" / "ck3-1.19.0.6.zh-hans.2560x1440.json"
)


def contract_sha256() -> str:
    return hashlib.sha256(UI_CONTRACT.read_bytes()).hexdigest()


def span(
    text: str,
    center: tuple[int, int],
    bbox: tuple[int, int, int, int],
    score: float = 0.9,
) -> OcrSpan:
    return OcrSpan(
        text=text,
        normalized=normalize_visible_text(text),
        score=score,
        center=center,
        bbox=bbox,
    )


def observation(
    screen: str,
    anchors: tuple[VisibleAnchor, ...],
    *,
    spans: tuple[OcrSpan, ...] = (),
    controls: tuple[VisibleControl, ...] = (),
    sequence: int = 1,
    monotonic: float | None = None,
    suffix: str = "1",
) -> Observation:
    return Observation(
        observation_id=suffix * 32,
        frame_id=("f" + suffix * 31)[:32],
        captured_at="2026-08-22T00:00:00+00:00",
        screen=screen,
        pid=10,
        hwnd=20,
        client_rect=(0, 0, 2560, 1440),
        screenshot="private.png",
        screenshot_sha256="a" * 64,
        spans=spans,
        anchors=anchors,
        controls=controls,
        confidence=0.9,
        capture_sequence=sequence,
        captured_monotonic=(float(sequence) if monotonic is None else monotonic),
        audit_path=f"frame-{sequence}.observation.json",
    )


def screen_probe_image(contract: UiContract, screen_id: str) -> Image.Image:
    image = Image.new("RGB", contract.resolution, (0, 0, 0))
    screen = next(item for item in contract.screens if item.screen_id == screen_id)
    for probe in screen.pixel_probes:
        colour = tuple(
            round((minimum + maximum) / 2)
            for minimum, maximum in zip(probe.mean_rgb_min, probe.mean_rgb_max)
        )
        image.paste(colour, probe.rect)
    return image


def main_menu_image(contract: UiContract) -> Image.Image:
    return screen_probe_image(contract, "main_menu")


def stable_pair(
    screen: str,
    *,
    spans: tuple[OcrSpan, ...] = (),
    controls: tuple[VisibleControl, ...] = (),
    start: int = 1,
) -> StableObservation:
    return StableObservation(
        screen,
        (
            observation(
                screen,
                (),
                spans=spans,
                controls=controls,
                sequence=start,
                suffix="a",
            ),
            observation(
                screen,
                (),
                spans=spans,
                controls=controls,
                sequence=start + 1,
                suffix="b",
            ),
        ),
    )


class UiClassifierTests(unittest.TestCase):
    def test_contract_hash_and_exact_canonical_semantics(self) -> None:
        digest = contract_sha256()
        contract = load_ui_contract(UI_CONTRACT, expected_sha256=digest)
        require_canonical_phase_b_contract(contract, digest)
        self.assertEqual(contract.source_sha256, digest)
        with self.assertRaisesRegex(AgentError, "SHA-256"):
            load_ui_contract(UI_CONTRACT, expected_sha256="0" * 64)

    def test_main_menu_requires_three_distinct_visible_spans(self) -> None:
        contract = load_ui_contract(UI_CONTRACT)
        spans = (
            span("继续游戏", (599, 477), (548, 463, 652, 491), 0.80),
            span("新游戏", (600, 557), (560, 543, 640, 571), 0.75),
            span("载入游戏", (600, 637), (548, 624, 652, 650), 0.76),
        )
        screen, confidence, reasons, anchors = contract.classify(
            spans, main_menu_image(contract)
        )
        self.assertEqual(screen, "main_menu")
        self.assertEqual(reasons, ())
        self.assertEqual(len(anchors), 3)
        self.assertAlmostEqual(confidence, 0.77, places=2)

    def test_main_menu_pixel_probe_and_modal_blockers_fail_closed(self) -> None:
        contract = load_ui_contract(UI_CONTRACT)
        spans = (
            span("继续游戏", (599, 477), (548, 463, 652, 491), 0.80),
            span("新游戏", (600, 557), (560, 543, 640, 571), 0.75),
            span("载入游戏", (600, 637), (548, 624, 652, 650), 0.76),
        )
        self.assertEqual(contract.classify(spans)[0], "unknown")
        wrong = Image.new("RGB", contract.resolution, "white")
        screen, _, reasons, _ = contract.classify(spans, wrong)
        self.assertEqual(screen, "unknown")
        self.assertIn("pixel:", reasons[0])
        modal = (*spans, span("开始教程", (1270, 820), (1200, 800, 1340, 840)))
        screen, _, reasons, _ = contract.classify(modal, main_menu_image(contract))
        self.assertEqual(screen, "unknown")
        self.assertIn("negative:modal.tutorial", reasons[0])

    def test_transition_and_modal_like_lobby_frames_remain_unknown(self) -> None:
        contract = load_ui_contract(UI_CONTRACT)
        cases = (
            (
                span("新游戏", (600, 557), (560, 543, 640, 571)),
                span("公爵罗贝尔", (1562, 1212), (1500, 1190, 1624, 1234)),
            ),
            (
                span("选择初始日期和角色", (479, 35), (350, 20, 608, 50)),
                span("公爵罗贝尔", (1561, 1203), (1500, 1180, 1622, 1226)),
                span("欢迎来到十字军之王III", (1270, 420), (1100, 390, 1440, 450)),
            ),
        )
        for spans in cases:
            with self.subTest(spans=spans):
                self.assertEqual(contract.classify(spans)[0], "unknown")

    def test_stable_bookmark_requires_top_central_and_robert_anchors(self) -> None:
        contract = load_ui_contract(UI_CONTRACT)
        spans = (
            span("选择初始日期和角色", (479, 35), (350, 20, 608, 50)),
            span("公爵弗拉季斯拉夫", (1418, 480), (1320, 460, 1516, 500)),
            span("公爵罗贝尔", (1561, 1203), (1500, 1180, 1622, 1226)),
        )
        lobby = screen_probe_image(contract, "bookmark_lobby")
        self.assertEqual(contract.classify(spans, lobby)[0], "bookmark_lobby")
        covered = lobby.copy()
        covered.paste((20, 20, 20), (900, 300, 1230, 1030))
        screen, _, reasons, _ = contract.classify(spans, covered)
        self.assertEqual(screen, "unknown")
        self.assertIn("pixel:lobby.", reasons[0])

    def test_one_ocr_span_cannot_satisfy_two_anchors(self) -> None:
        contract = UiContract(
            format_version=1,
            game_version="1.19.0.6",
            language="l_simp_chinese",
            resolution=(2560, 1440),
            screens=(
                ScreenSpec(
                    "bad_rules",
                    (
                        AnchorSpec("rules.title", "游戏规则", (0, 0, 1, 1), True),
                        AnchorSpec(
                            "rules.filter", "游戏规则过滤器", (0, 0, 1, 1), True
                        ),
                    ),
                ),
            ),
            controls=(),
            forbidden_capabilities=frozenset(),
        )
        only = span("游戏规则过滤器", (1000, 200), (900, 180, 1100, 220))
        screen_id, _, reasons, _ = contract.classify((only,))
        self.assertEqual(screen_id, "unknown")
        self.assertIn("reuses-visible-span", reasons[0])

    def test_forbidden_registered_control_and_string_boolean_are_rejected(self) -> None:
        payload = json.loads(UI_CONTRACT.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="xar-ui-contract-") as temporary:
            path = Path(temporary) / "ui.json"
            payload["forbidden_capabilities"].append("main_menu.new_game")
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(AgentError, "forbidden capability"):
                load_ui_contract(path)
            payload["forbidden_capabilities"].remove("main_menu.new_game")
            payload["screens"][0]["anchors"][0]["contains"] = "false"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(AgentError, "must be a boolean"):
                load_ui_contract(path)

    def test_hash_valid_semantically_substituted_contract_is_rejected(self) -> None:
        payload = json.loads(UI_CONTRACT.read_text(encoding="utf-8"))
        payload["screens"][0]["pixel_probes"][0]["mean_rgb_min"][0] += 1
        with tempfile.TemporaryDirectory(prefix="xar-ui-substitution-") as temporary:
            path = Path(temporary) / "ui.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            contract = load_ui_contract(path, expected_sha256=digest)
            with self.assertRaisesRegex(AgentError, "exact canonical"):
                require_canonical_phase_b_contract(contract, digest)

    def test_historical_bookmark_and_modal_frames_replay(self) -> None:
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        root = Path(
            os.environ.get(
                "XAR_HISTORICAL_UI_FIXTURE_ROOT",
                str(
                    local
                    / "Temp"
                    / "opencode"
                    / "xar_terminal_observer_nondebug3_20260821"
                ),
            )
        )
        modal = Path(
            os.environ.get(
                "XAR_HISTORICAL_UI_MODAL_FIXTURE",
                str(
                    local
                    / "Temp"
                    / "opencode"
                    / "ervc_acceptance_dev_original_then_vivhite_20260821_1"
                    / "cells"
                    / "original-then-vivhite"
                    / "02_bookmark.png"
                ),
            )
        )
        cases = (
            (root / "02_bookmark.png", "unknown"),
            (root / "03_start_enabled.png", "bookmark_lobby"),
            (root / "03_ruler_selected.png", "bookmark_lobby"),
            (modal, "unknown"),
        )
        missing = [str(path) for path, _expected in cases if not path.is_file()]
        if missing:
            self.skipTest(f"historical local UI fixtures unavailable: {missing!r}")
        contract = load_ui_contract(UI_CONTRACT)
        for path, expected in cases:
            with self.subTest(path=path):
                with Image.open(path) as opened:
                    image = opened.convert("RGB")
                self.assertEqual(
                    contract.classify(ocr_spans(image), image)[0], expected
                )


class WindowBindingTests(unittest.TestCase):
    def _session(self, executable: Path) -> object:
        process = mock.Mock(pid=123)
        process.poll.return_value = None
        process.image_path.return_value = str(executable)
        return types.SimpleNamespace(process=process, ck3_creation_date="created")

    def test_empty_wmi_executable_uses_pinned_process_handle_image(self) -> None:
        executable = Path("C:/game/binaries/ck3.exe")
        identity = {
            "pid": 123,
            "parent_pid": os.getpid(),
            "name": "ck3.exe",
            "creation_date": "created",
            "executable": "",
        }
        with mock.patch(
            "xar_autoplayer.runtime._process_identity", return_value=identity
        ), mock.patch(
            "xar_autoplayer.vision.window._eligible_windows",
            return_value=[(456, (0, 0, 2560, 1440))],
        ):
            binding = BoundGameWindow.bind_session(
                self._session(executable), executable
            )
            binding.verify_process()
            audit = binding.audit_binding()
        self.assertEqual(audit["process"]["wmi_executable"], "")
        self.assertEqual(audit["process"]["handle_executable"], str(executable))

    def test_nonempty_wmi_executable_and_direct_parent_are_strict(self) -> None:
        executable = Path("C:/game/binaries/ck3.exe")
        base = {
            "pid": 123,
            "parent_pid": os.getpid(),
            "name": "ck3.exe",
            "creation_date": "created",
            "executable": "C:/other/ck3.exe",
        }
        with mock.patch(
            "xar_autoplayer.runtime._process_identity", return_value=base
        ):
            with self.assertRaisesRegex(AgentError, "unauthenticated"):
                BoundGameWindow.bind_session(self._session(executable), executable)
        base["executable"] = str(executable)
        base["parent_pid"] = os.getpid() + 1
        with mock.patch(
            "xar_autoplayer.runtime._process_identity", return_value=base
        ):
            with self.assertRaisesRegex(AgentError, "unauthenticated"):
                BoundGameWindow.bind_session(self._session(executable), executable)

    def test_acquire_foreground_never_synthesizes_alt_or_focus(self) -> None:
        binding = object.__new__(BoundGameWindow)
        with mock.patch.object(BoundGameWindow, "require_foreground") as require:
            binding.acquire_foreground()
        require.assert_called_once_with()

    @staticmethod
    def _foreground_binding() -> BoundGameWindow:
        process = mock.Mock()
        process.poll.return_value = None
        process.image_path.return_value = "C:/game/binaries/ck3.exe"
        return BoundGameWindow(
            process=process,
            pid=10,
            hwnd=20,
            client_rect=(0, 0, 2560, 1440),
            executable="C:/game/binaries/ck3.exe",
            creation_date="created",
            parent_pid=9,
        )

    def _foreground_context(self, *, attach_results=(True, True)):
        import contextlib

        state = {"foreground": 30}
        set_foreground = mock.Mock()

        def identity(hwnd: int):
            return (100, 10) if int(hwnd) == 20 else (300, 30)

        attach = mock.Mock(side_effect=list(attach_results))
        attach.argtypes = None
        attach.restype = None
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch("ctypes.WinDLL", return_value=types.SimpleNamespace(AttachThreadInput=attach)))
        stack.enter_context(mock.patch("ctypes.set_last_error"))
        stack.enter_context(mock.patch("ctypes.get_last_error", return_value=5))
        stack.enter_context(mock.patch("win32api.GetCurrentThreadId", return_value=200))
        stack.enter_context(mock.patch("win32api.GetLastInputInfo", return_value=500))
        stack.enter_context(
            mock.patch("win32gui.GetForegroundWindow", side_effect=lambda: state["foreground"])
        )
        stack.enter_context(mock.patch("win32gui.SetForegroundWindow", set_foreground))
        stack.enter_context(mock.patch("win32gui.IsWindow", return_value=True))
        stack.enter_context(mock.patch("win32gui.IsWindowVisible", return_value=True))
        stack.enter_context(mock.patch("win32process.GetWindowThreadProcessId", side_effect=identity))
        stack.enter_context(mock.patch("xar_autoplayer.vision.window._root_window", side_effect=lambda hwnd: hwnd))
        stack.enter_context(
            mock.patch(
                "xar_autoplayer.vision.window._client_rect",
                return_value=(0, 0, 2560, 1440),
            )
        )
        return stack, state, set_foreground, attach

    def test_foreground_direct_success_is_single_no_input_transaction(self) -> None:
        binding = self._foreground_binding()
        stack, state, set_foreground, attach = self._foreground_context()
        set_foreground.side_effect = lambda hwnd: state.update(foreground=int(hwnd))
        with stack, mock.patch.object(BoundGameWindow, "verify", return_value={}):
            result = binding.request_foreground_without_input()
        self.assertEqual(result["mode"], "direct")
        self.assertFalse(result["synthetic_input"])
        self.assertTrue(result["observed_last_input_tick_unchanged"])
        set_foreground.assert_called_once_with(20)
        attach.assert_not_called()

    def test_foreground_direct_success_accepts_initially_null_foreground(self) -> None:
        binding = self._foreground_binding()
        stack, state, set_foreground, attach = self._foreground_context()
        state["foreground"] = 0
        set_foreground.side_effect = lambda hwnd: state.update(foreground=int(hwnd))
        with stack, mock.patch.object(BoundGameWindow, "verify", return_value={}):
            result = binding.request_foreground_without_input()
        self.assertEqual(result["mode"], "direct")
        self.assertEqual(
            (
                result["foreground_hwnd_before"],
                result["foreground_thread_id_before"],
                result["foreground_pid_before"],
            ),
            (0, 0, 0),
        )
        set_foreground.assert_called_once_with(20)
        attach.assert_not_called()

    def test_foreground_fallback_rejects_changed_initial_foreground(self) -> None:
        binding = self._foreground_binding()
        stack, state, set_foreground, attach = self._foreground_context()
        set_foreground.side_effect = lambda _hwnd: state.update(foreground=40)
        with stack, mock.patch.object(BoundGameWindow, "verify", return_value={}):
            with self.assertRaisesRegex(AgentError, "fallback precondition"):
                binding.request_foreground_without_input()
        set_foreground.assert_called_once_with(20)
        attach.assert_not_called()

    def test_foreground_attached_fallback_requires_exact_attach_detach_pair(self) -> None:
        binding = self._foreground_binding()
        stack, state, set_foreground, attach = self._foreground_context()

        def activate(hwnd: int) -> None:
            if set_foreground.call_count == 2:
                state["foreground"] = int(hwnd)

        set_foreground.side_effect = activate
        with stack, mock.patch.object(BoundGameWindow, "verify", return_value={}):
            result = binding.request_foreground_without_input()
        self.assertEqual(result["mode"], "attached_fallback")
        self.assertTrue(result["detach_succeeded"])
        self.assertEqual(
            attach.call_args_list,
            [mock.call(200, 300, True), mock.call(200, 300, False)],
        )
        self.assertEqual(set_foreground.call_count, 2)

    def test_foreground_attached_critical_section_never_runs_full_verify(self) -> None:
        binding = self._foreground_binding()
        stack, state, set_foreground, attach = self._foreground_context()
        attached = {"value": False}

        def attach_pair(_caller: int, _foreground: int, join: bool) -> bool:
            attached["value"] = bool(join)
            return True

        def verify() -> dict[str, object]:
            if attached["value"]:
                raise AssertionError("full process/WMI verify ran while queues attached")
            return {}

        attach.side_effect = attach_pair

        def activate(hwnd: int) -> None:
            if set_foreground.call_count == 2:
                state["foreground"] = int(hwnd)

        set_foreground.side_effect = activate
        with stack, mock.patch.object(
            BoundGameWindow, "verify", side_effect=verify
        ) as full_verify:
            result = binding.request_foreground_without_input()
        self.assertEqual(result["mode"], "attached_fallback")
        self.assertFalse(attached["value"])
        self.assertGreaterEqual(full_verify.call_count, 3)
        self.assertEqual(
            attach.call_args_list,
            [mock.call(200, 300, True), mock.call(200, 300, False)],
        )

    def test_foreground_attach_or_detach_failure_is_not_retried(self) -> None:
        for label, results, expected_calls in (
            ("attach", (False,), 1),
            ("detach", (True, False), 2),
        ):
            with self.subTest(label=label):
                binding = self._foreground_binding()
                stack, state, set_foreground, attach = self._foreground_context(
                    attach_results=results
                )

                def activate(hwnd: int) -> None:
                    if set_foreground.call_count == 2:
                        state["foreground"] = int(hwnd)

                set_foreground.side_effect = activate
                with stack, mock.patch.object(BoundGameWindow, "verify", return_value={}):
                    with self.assertRaisesRegex(AgentError, f"(?i){label}"):
                        binding.request_foreground_without_input()
                self.assertEqual(attach.call_count, expected_calls)
                self.assertLessEqual(set_foreground.call_count, 2)

    def test_foreground_direct_api_exception_never_falls_back(self) -> None:
        binding = self._foreground_binding()
        stack, _state, set_foreground, attach = self._foreground_context()
        set_foreground.side_effect = OSError("direct failure")
        with stack, mock.patch.object(BoundGameWindow, "verify", return_value={}):
            with self.assertRaisesRegex(AgentError, "direct foreground"):
                binding.request_foreground_without_input()
        set_foreground.assert_called_once_with(20)
        attach.assert_not_called()

    def test_foreground_async_attach_boundaries_attempt_one_exact_detach(self) -> None:
        for label, results, expected_set_calls in (
            ("attach-return-gap", (KeyboardInterrupt(), True), 1),
            ("detach-return-gap", (True, KeyboardInterrupt()), 2),
        ):
            with self.subTest(label=label):
                binding = self._foreground_binding()
                stack, state, set_foreground, attach = self._foreground_context(
                    attach_results=results
                )

                def activate(hwnd: int) -> None:
                    if set_foreground.call_count == 2:
                        state["foreground"] = int(hwnd)

                set_foreground.side_effect = activate
                with stack, mock.patch.object(
                    BoundGameWindow, "verify", return_value={}
                ):
                    with self.assertRaises(KeyboardInterrupt):
                        binding.request_foreground_without_input()
                self.assertEqual(
                    attach.call_args_list,
                    [mock.call(200, 300, True), mock.call(200, 300, False)],
                )
                self.assertEqual(set_foreground.call_count, expected_set_calls)


class UiDriverSafetyTests(unittest.TestCase):
    @staticmethod
    def _binding() -> dict[str, object]:
        return {
            "process": {
                "pid": 10,
                "parent_pid": 9,
                "name": "ck3.exe",
                "creation_date": "20260822000000.000000+000",
                "executable": "C:/game/binaries/ck3.exe",
                "wmi_executable": "",
                "handle_executable": "C:/game/binaries/ck3.exe",
            },
            "window": {
                "hwnd": 20,
                "client_rect": [0, 0, 2560, 1440],
                "client_size": [2560, 1440],
            },
        }

    def _prepare_window(self, window: mock.Mock) -> None:
        window.client_rect = (0, 0, 2560, 1440)
        window.audit_binding.return_value = self._binding()

    def _driver(self, root: Path) -> tuple[VisibleUiDriver, ControlSpec, OcrSpan, str]:
        artifacts = root / "state" / "runs" / "run-1" / "artifacts"
        artifacts.mkdir(parents=True)
        driver = object.__new__(VisibleUiDriver)
        driver.artifacts = artifacts
        driver._sequence = 0
        driver._capture_sequence = 0
        driver._input_budget_consumed = False
        driver._issued = {}
        driver._session_nonce = "session"
        driver._secret = b"secret"
        driver._contract_sha256 = "d" * 64
        driver._test_events = []

        def durable(event: dict[str, object]) -> str:
            driver._test_events.append(event)
            return hashlib.sha256(
                json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()

        driver._durable_event_callback = durable
        spec = ControlSpec(
            "main_menu.new_game",
            "main_menu",
            "新游戏",
            "新游戏",
            (0.18, 0.36, 0.30, 0.42),
            "bookmark_lobby",
            "reversible",
        )
        driver.contract = UiContract(
            1,
            "1.19.0.6",
            "l_simp_chinese",
            (2560, 1440),
            (),
            (spec,),
            frozenset({"bookmark_lobby.start_game"}),
        )
        target = span("新游戏", (600, 557), (560, 543, 640, 571))
        token = "c" * 64
        before = observation(
            "main_menu",
            (),
            spans=(target,),
            controls=(
                VisibleControl(
                    "main_menu.new_game", "新游戏", token, target.bbox, target.center
                ),
            ),
            sequence=2,
            suffix="b",
        )
        first = observation(
            "main_menu",
            (),
            spans=(target,),
            controls=before.controls,
            sequence=1,
            suffix="a",
        )
        stable = StableObservation("main_menu", (first, before))
        driver._issued[token] = _IssuedControl(
            before, spec, target, time.monotonic(), stable
        )
        return driver, spec, target, token

    def test_constructor_binds_exact_hash_and_capture_uses_relative_evidence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-capture-") as temporary:
            root = Path(temporary)
            artifacts = root / "state" / "runs" / "run-1" / "artifacts"
            artifacts.mkdir(parents=True)
            digest = contract_sha256()
            contract = load_ui_contract(UI_CONTRACT, expected_sha256=digest)
            window = mock.Mock(pid=10, hwnd=20)
            window.client_rect = (0, 0, 2560, 1440)
            window.capture.return_value = main_menu_image(contract)
            driver = VisibleUiDriver(
                window,
                contract,
                artifacts,
                expected_game_version="1.19.0.6",
                expected_language="l_simp_chinese",
                expected_contract_sha256=digest,
                durable_event_callback=lambda _event: "e" * 64,
            )
            with mock.patch(
                "xar_autoplayer.control.executor.ocr_spans",
                return_value=(
                    span("继续游戏", (599, 477), (548, 463, 652, 491), 0.80),
                    span("新游戏", (600, 557), (560, 543, 640, 571), 0.75),
                    span("载入游戏", (600, 637), (548, 624, 652, 650), 0.76),
                ),
            ):
                captured = driver._capture_observation()
            self.assertEqual(captured.screen, "main_menu")
            self.assertTrue(captured.screenshot.startswith("artifacts/"))
            self.assertTrue(captured.audit_path.startswith("artifacts/"))
            self.assertTrue((artifacts.parent / captured.screenshot).is_file())
            self.assertTrue((artifacts.parent / captured.audit_path).is_file())
            with self.assertRaisesRegex(AgentError, "exact canonical"):
                VisibleUiDriver(
                    window,
                    contract,
                    artifacts,
                    expected_game_version="1.19.0.6",
                    expected_language="l_simp_chinese",
                    expected_contract_sha256="0" * 64,
                    durable_event_callback=lambda _event: "e" * 64,
                )

    def test_win32_left_click_is_one_two_record_sendinput_batch(self) -> None:
        send_input = mock.Mock(return_value=2)
        user32 = types.SimpleNamespace(SendInput=send_input)
        with mock.patch(
            "xar_autoplayer.control.executor.ctypes.WinDLL", return_value=user32
        ):
            submit = _prepare_left_click_batch()
            send_input.assert_not_called()
            submit()
        send_input.assert_called_once()
        count, records, record_size = send_input.call_args.args
        self.assertEqual(count, 2)
        self.assertGreater(record_size, 0)
        self.assertEqual(records[0].mi.dwFlags, _MOUSEEVENTF_LEFTDOWN)
        self.assertEqual(records[1].mi.dwFlags, _MOUSEEVENTF_LEFTUP)

    def test_anchor_motion_prevents_false_two_frame_stability(self) -> None:
        driver = object.__new__(VisibleUiDriver)
        first = observation(
            "bookmark_lobby",
            (VisibleAnchor("lobby.title", "title", 0.9, (0, 0, 10, 10), (5, 5)),),
            sequence=1,
            suffix="a",
        )
        moved = observation(
            "bookmark_lobby",
            (VisibleAnchor("lobby.title", "title", 0.9, (30, 0, 40, 10), (35, 5)),),
            sequence=2,
            suffix="b",
        )
        stable = observation(
            "bookmark_lobby",
            (VisibleAnchor("lobby.title", "title", 0.9, (31, 0, 41, 10), (36, 5)),),
            sequence=3,
            suffix="c",
        )
        with mock.patch.object(
            driver, "_capture_observation", side_effect=[first, moved, stable]
        ), mock.patch("xar_autoplayer.control.executor.time.sleep"):
            result = driver.observe_stable("bookmark_lobby", 2, stable_frames=2)
        self.assertIsInstance(result, StableObservation)
        self.assertEqual(result.frames, (moved, stable))

    def test_expired_token_causes_zero_input(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-expired-") as temporary:
            driver, spec, target, token = self._driver(Path(temporary))
            driver._issued[token] = _IssuedControl(
                driver._issued[token].observation,
                spec,
                target,
                time.monotonic() - 60,
            )
            with self.assertRaisesRegex(AgentError, "expired"):
                driver.click_visible_control(token, timeout_seconds=1)

    def test_token_expiring_during_durable_receipt_causes_zero_input(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-late-expiry-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            issued_at = driver._issued[token].issued_monotonic
            fresh = observation("main_menu", (), spans=(target,))
            hover = observation("main_menu", (), spans=(target,))
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            self._prepare_window(window)
            driver.window = window
            fake_gui = types.SimpleNamespace(FAILSAFE=True, moveTo=mock.Mock())
            send_click = mock.Mock()
            with mock.patch.object(
                driver, "_capture_observation", return_value=fresh
            ), mock.patch.object(
                driver,
                "_capture_observation_with_image",
                return_value=(hover, hover_image),
            ), mock.patch.dict(sys.modules, {"pyautogui": fake_gui}), mock.patch(
                "xar_autoplayer.control.executor._prepare_left_click_batch",
                return_value=send_click,
            ), mock.patch(
                "xar_autoplayer.control.executor.time.sleep"
            ), mock.patch(
                "xar_autoplayer.control.executor.time.monotonic",
                side_effect=[issued_at + 1.0, issued_at + 6.0],
            ):
                with self.assertRaisesRegex(AgentError, "immediately before input"):
                    driver.click_visible_control(token, timeout_seconds=1)
            send_click.assert_not_called()
            window.capture_patch.assert_not_called()
            receipt = json.loads(
                next(driver.artifacts.glob("*action*.json")).read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], "failed_after_possible_input")
            self.assertTrue(receipt["input_may_have_occurred"])
            self.assertFalse(receipt["button_click_may_have_occurred"])

    def test_token_expiring_during_final_guards_causes_zero_input(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-final-expiry-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            issued_at = driver._issued[token].issued_monotonic
            fresh = observation("main_menu", (), spans=(target,))
            hover = observation("main_menu", (), spans=(target,))
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            self._prepare_window(window)
            window.capture_patch.side_effect = lambda bbox: hover_image.crop(bbox)
            driver.window = window
            fake_gui = types.SimpleNamespace(FAILSAFE=True, moveTo=mock.Mock())
            send_click = mock.Mock()
            with mock.patch.object(
                driver, "_capture_observation", return_value=fresh
            ), mock.patch.object(
                driver,
                "_capture_observation_with_image",
                return_value=(hover, hover_image),
            ), mock.patch.dict(sys.modules, {"pyautogui": fake_gui}), mock.patch(
                "xar_autoplayer.control.executor._prepare_left_click_batch",
                return_value=send_click,
            ), mock.patch(
                "xar_autoplayer.control.executor.time.sleep"
            ), mock.patch(
                "xar_autoplayer.control.executor.time.monotonic",
                side_effect=[issued_at + 1.0, issued_at + 2.0, issued_at + 6.0],
            ):
                with self.assertRaisesRegex(AgentError, "at input submission"):
                    driver.click_visible_control(token, timeout_seconds=1)
            send_click.assert_not_called()
            self.assertEqual(window.require_cursor_target.call_count, 2)
            receipt = json.loads(
                next(driver.artifacts.glob("*action*.json")).read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], "failed_after_possible_input")
            self.assertTrue(receipt["input_may_have_occurred"])
            self.assertFalse(receipt["button_click_may_have_occurred"])

    def test_focus_or_overlay_change_after_hover_causes_zero_mouse_down(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-hover-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            fresh = observation("main_menu", (), spans=(target,))
            hover = observation("main_menu", (), spans=(target,))
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            self._prepare_window(window)
            window.require_cursor_target.side_effect = AgentError("focus changed")
            driver.window = window
            fake_gui = types.SimpleNamespace(
                FAILSAFE=True,
                moveTo=mock.Mock(),
                mouseDown=mock.Mock(),
                mouseUp=mock.Mock(),
            )
            send_click = mock.Mock()
            with mock.patch.object(
                driver, "_capture_observation", return_value=fresh
            ), mock.patch.object(
                driver,
                "_capture_observation_with_image",
                return_value=(hover, hover_image),
            ), mock.patch.dict(sys.modules, {"pyautogui": fake_gui}), mock.patch(
                "xar_autoplayer.control.executor._prepare_left_click_batch",
                return_value=send_click,
            ), mock.patch(
                "xar_autoplayer.control.executor.time.sleep"
            ):
                with self.assertRaisesRegex(AgentError, "focus changed"):
                    driver.click_visible_control(token, timeout_seconds=1)
            send_click.assert_not_called()
            receipt = json.loads(
                next(driver.artifacts.glob("*action*.json")).read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], "failed_after_possible_input")
            self.assertTrue(receipt["input_may_have_occurred"])
            self.assertFalse(receipt["button_click_may_have_occurred"])

    def test_postcondition_failure_keeps_durable_possible_input_receipt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-receipt-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            fresh = observation("main_menu", (), spans=(target,))
            hover = observation("main_menu", (), spans=(target,))
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            self._prepare_window(window)
            window.capture_patch.side_effect = lambda bbox: hover_image.crop(bbox)
            driver.window = window
            fake_gui = types.SimpleNamespace(
                FAILSAFE=True,
                moveTo=mock.Mock(),
                mouseDown=mock.Mock(),
                mouseUp=mock.Mock(),
            )
            send_click = mock.Mock(return_value=(2, 0))
            with mock.patch.object(
                driver, "_capture_observation", return_value=fresh
            ), mock.patch.object(
                driver,
                "_capture_observation_with_image",
                return_value=(hover, hover_image),
            ), mock.patch.object(
                driver,
                "observe_stable",
                side_effect=AgentError("postcondition timeout"),
            ), mock.patch.dict(sys.modules, {"pyautogui": fake_gui}), mock.patch(
                "xar_autoplayer.control.executor._prepare_left_click_batch",
                return_value=send_click,
            ), mock.patch(
                "xar_autoplayer.control.executor.time.sleep"
            ):
                with self.assertRaisesRegex(AgentError, "postcondition timeout"):
                    driver.click_visible_control(token, timeout_seconds=1)
            send_click.assert_called_once_with()
            fake_gui.mouseDown.assert_not_called()
            fake_gui.mouseUp.assert_not_called()
            receipt = json.loads(
                next(driver.artifacts.glob("*action*.json")).read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], "failed_after_possible_input")
            self.assertTrue(receipt["input_may_have_occurred"])
            event_kinds = [row["kind"] for row in driver._test_events]
            self.assertEqual(
                event_kinds,
                ["ui_action_planned", "ui_input_armed", "ui_action_finished"],
            )

    def test_target_patch_replacement_after_attempt_receipt_causes_zero_input(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-patch-change-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            fresh = observation("main_menu", (), spans=(target,))
            hover = observation("main_menu", (), spans=(target,))
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            self._prepare_window(window)

            def replacement_after_durable_attempt(
                bbox: tuple[int, int, int, int],
            ) -> Image.Image:
                receipt = json.loads(
                    next(driver.artifacts.glob("*action*.json")).read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(receipt["status"], "input_attempting")
                self.assertTrue(receipt["input_may_have_occurred"])
                event_kinds = [row["kind"] for row in driver._test_events]
                self.assertEqual(
                    event_kinds, ["ui_action_planned", "ui_input_armed"]
                )
                return Image.new(
                    "RGB", (bbox[2] - bbox[0], bbox[3] - bbox[1]), "white"
                )

            window.capture_patch.side_effect = replacement_after_durable_attempt
            driver.window = window
            fake_gui = types.SimpleNamespace(
                FAILSAFE=True,
                moveTo=mock.Mock(),
                mouseDown=mock.Mock(),
                mouseUp=mock.Mock(),
            )
            send_click = mock.Mock()
            with mock.patch.object(
                driver, "_capture_observation", return_value=fresh
            ), mock.patch.object(
                driver,
                "_capture_observation_with_image",
                return_value=(hover, hover_image),
            ), mock.patch.dict(sys.modules, {"pyautogui": fake_gui}), mock.patch(
                "xar_autoplayer.control.executor._prepare_left_click_batch",
                return_value=send_click,
            ), mock.patch(
                "xar_autoplayer.control.executor.time.sleep"
            ):
                with self.assertRaisesRegex(AgentError, "target pixels changed"):
                    driver.click_visible_control(token, timeout_seconds=1)
            send_click.assert_not_called()
            self.assertEqual(window.require_cursor_target.call_count, 1)
            receipt = json.loads(
                next(driver.artifacts.glob("*action*.json")).read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], "failed_after_possible_input")
            self.assertTrue(receipt["input_may_have_occurred"])
            self.assertFalse(receipt["button_click_may_have_occurred"])

    def test_final_cursor_guard_failure_after_patch_causes_zero_input(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-final-guard-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            fresh = observation("main_menu", (), spans=(target,))
            hover = observation("main_menu", (), spans=(target,))
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            self._prepare_window(window)
            window.capture_patch.side_effect = lambda bbox: hover_image.crop(bbox)
            window.require_cursor_target.side_effect = [
                None,
                AgentError("cursor target changed after final patch"),
            ]
            driver.window = window
            fake_gui = types.SimpleNamespace(
                FAILSAFE=True,
                moveTo=mock.Mock(),
                mouseDown=mock.Mock(),
                mouseUp=mock.Mock(),
            )
            send_click = mock.Mock()
            with mock.patch.object(
                driver, "_capture_observation", return_value=fresh
            ), mock.patch.object(
                driver,
                "_capture_observation_with_image",
                return_value=(hover, hover_image),
            ), mock.patch.dict(sys.modules, {"pyautogui": fake_gui}), mock.patch(
                "xar_autoplayer.control.executor._prepare_left_click_batch",
                return_value=send_click,
            ), mock.patch(
                "xar_autoplayer.control.executor.time.sleep"
            ):
                with self.assertRaisesRegex(AgentError, "cursor target changed"):
                    driver.click_visible_control(token, timeout_seconds=1)
            send_click.assert_not_called()

    def test_success_receipt_binds_wal_identity_stable_frames_and_patch_artifacts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-success-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            fresh = observation(
                "main_menu", (), spans=(target,), sequence=3, suffix="c"
            )
            hover = observation(
                "main_menu", (), spans=(target,), sequence=4, suffix="d"
            )
            after = stable_pair("bookmark_lobby", start=5)
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            self._prepare_window(window)
            window.capture_patch.side_effect = lambda bbox: hover_image.crop(bbox)
            driver.window = window

            def assert_wal_before_move(*_args: object, **_kwargs: object) -> None:
                self.assertEqual(
                    [row["kind"] for row in driver._test_events],
                    ["ui_action_planned", "ui_input_armed"],
                )

            fake_gui = types.SimpleNamespace(
                FAILSAFE=True,
                moveTo=mock.Mock(side_effect=assert_wal_before_move),
            )
            send_click = mock.Mock(return_value=(2, 0))
            with mock.patch.object(
                driver, "_capture_observation", return_value=fresh
            ), mock.patch.object(
                driver,
                "_capture_observation_with_image",
                return_value=(hover, hover_image),
            ), mock.patch.object(
                driver, "observe_stable", return_value=after
            ), mock.patch.dict(
                sys.modules, {"pyautogui": fake_gui}
            ), mock.patch(
                "xar_autoplayer.control.executor._prepare_left_click_batch",
                return_value=send_click,
            ), mock.patch(
                "xar_autoplayer.control.executor.time.sleep"
            ):
                response = driver.click_visible_control(token, timeout_seconds=1)

            action = response["action"]
            self.assertEqual(action["status"], "confirmed")
            self.assertEqual(action["contract_sha256"], "d" * 64)
            self.assertEqual(action["binding"]["process"]["pid"], 10)
            self.assertEqual(action["binding"]["window"]["hwnd"], 20)
            self.assertEqual(
                action["send_input"],
                {"requested": 2, "accepted": 2, "last_error": 0},
            )
            self.assertEqual(action["before_stable_observation"]["stable_frames"], 2)
            self.assertEqual(action["after_stable_observation"]["stable_frames"], 2)
            self.assertEqual(
                action["target"]["hover"]["patch_sha256"],
                action["target"]["final_patch_sha256"],
            )
            for label in ("hover_patch_artifact", "final_patch_artifact"):
                artifact = action["target"][label]
                self.assertTrue(str(artifact["path"]).startswith("artifacts/"))
                path = driver.artifacts.parent / str(artifact["path"])
                self.assertTrue(path.is_file())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), artifact["sha256"])
            self.assertEqual(
                [row["kind"] for row in driver._test_events],
                ["ui_action_planned", "ui_input_armed", "ui_action_finished"],
            )
            self.assertEqual(
                set(driver._test_events[1]["target"]), {"issued", "fresh"}
            )
            send_click.assert_called_once_with()
            with self.assertRaisesRegex(AgentError, "budget"):
                driver.click_visible_control(token, timeout_seconds=1)

    def test_armed_wal_failure_prevents_cursor_move_and_sendinput(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-wal-fail-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            fresh = observation(
                "main_menu", (), spans=(target,), sequence=3, suffix="c"
            )
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            self._prepare_window(window)
            driver.window = window
            events: list[str] = []

            def durable(event: dict[str, object]) -> str:
                events.append(str(event["kind"]))
                if event["kind"] == "ui_input_armed":
                    raise AgentError("WAL fsync failed")
                return "e" * 64

            driver._durable_event_callback = durable
            fake_gui = types.SimpleNamespace(FAILSAFE=True, moveTo=mock.Mock())
            send_click = mock.Mock(return_value=(2, 0))
            with mock.patch.object(
                driver, "_capture_observation", return_value=fresh
            ), mock.patch.object(
                driver,
                "_capture_observation_with_image",
                return_value=(fresh, hover_image),
            ), mock.patch.dict(
                sys.modules, {"pyautogui": fake_gui}
            ), mock.patch(
                "xar_autoplayer.control.executor._prepare_left_click_batch",
                return_value=send_click,
            ):
                with self.assertRaisesRegex(AgentError, "WAL fsync failed"):
                    driver.click_visible_control(token, timeout_seconds=1)
            fake_gui.moveTo.assert_not_called()
            send_click.assert_not_called()
            receipt = json.loads(
                next(driver.artifacts.glob("*action*.json")).read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], "failed_after_possible_input")
            self.assertTrue(receipt["input_may_have_occurred"])
            self.assertEqual(
                events,
                ["ui_action_planned", "ui_input_armed"],
            )

    def test_committed_armed_wal_then_callback_error_never_moves_or_retries_event(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-wal-commit-error-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            fresh = observation(
                "main_menu", (), spans=(target,), sequence=3, suffix="c"
            )
            window = mock.Mock()
            self._prepare_window(window)
            driver.window = window
            events: list[dict[str, object]] = []

            def durable(event: dict[str, object]) -> str:
                events.append(event)
                if event["kind"] == "ui_input_armed":
                    raise OSError("committed armed WAL callback failed")
                return "e" * 64

            driver._durable_event_callback = durable
            fake_gui = types.SimpleNamespace(FAILSAFE=True, moveTo=mock.Mock())
            send_click = mock.Mock(return_value=(2, 0))
            with mock.patch.object(
                driver, "_capture_observation", return_value=fresh
            ), mock.patch.dict(sys.modules, {"pyautogui": fake_gui}), mock.patch(
                "xar_autoplayer.control.executor._prepare_left_click_batch",
                return_value=send_click,
            ):
                with self.assertRaisesRegex(AgentError, "committed armed WAL"):
                    driver.click_visible_control(token, timeout_seconds=1)
            fake_gui.moveTo.assert_not_called()
            send_click.assert_not_called()
            self.assertEqual(
                [event["kind"] for event in events],
                ["ui_action_planned", "ui_input_armed"],
            )
            receipt = json.loads(
                next(driver.artifacts.glob("*action*.json")).read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], "failed_after_possible_input")
            self.assertTrue(receipt["input_may_have_occurred"])
            self.assertTrue(receipt["pointer_input_may_have_occurred"])
            self.assertFalse(receipt["button_click_may_have_occurred"])

    def test_committed_planned_wal_then_callback_error_is_zero_input_one_event(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-planned-commit-error-") as temporary:
            driver, _spec, _target, token = self._driver(Path(temporary))
            window = mock.Mock()
            self._prepare_window(window)
            driver.window = window
            events: list[dict[str, object]] = []

            def durable(event: dict[str, object]) -> str:
                events.append(event)
                raise OSError("committed planned WAL callback failed")

            driver._durable_event_callback = durable
            with self.assertRaisesRegex(AgentError, "committed planned WAL"):
                driver.click_visible_control(token, timeout_seconds=1)
            self.assertEqual(
                [event["kind"] for event in events], ["ui_action_planned"]
            )
            receipt = json.loads(
                next(driver.artifacts.glob("*action*.json")).read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], "rejected_before_input")
            self.assertFalse(receipt["input_may_have_occurred"])
            self.assertFalse(receipt["pointer_input_may_have_occurred"])
            self.assertFalse(receipt["button_click_may_have_occurred"])

    def test_committed_finished_wal_then_callback_error_keeps_confirmed_once(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-finished-commit-error-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            fresh = observation(
                "main_menu", (), spans=(target,), sequence=3, suffix="c"
            )
            hover = observation(
                "main_menu", (), spans=(target,), sequence=4, suffix="d"
            )
            after = stable_pair("bookmark_lobby", start=5)
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            self._prepare_window(window)
            window.capture_patch.side_effect = lambda bbox: hover_image.crop(bbox)
            driver.window = window
            events: list[dict[str, object]] = []

            def durable(event: dict[str, object]) -> str:
                events.append(event)
                if event["kind"] == "ui_action_finished":
                    raise OSError("committed finished WAL callback failed")
                return "e" * 64

            driver._durable_event_callback = durable
            fake_gui = types.SimpleNamespace(FAILSAFE=True, moveTo=mock.Mock())
            send_click = mock.Mock(return_value=(2, 0))
            with mock.patch.object(
                driver, "_capture_observation", return_value=fresh
            ), mock.patch.object(
                driver,
                "_capture_observation_with_image",
                return_value=(hover, hover_image),
            ), mock.patch.object(
                driver, "observe_stable", return_value=after
            ), mock.patch.dict(
                sys.modules, {"pyautogui": fake_gui}
            ), mock.patch(
                "xar_autoplayer.control.executor._prepare_left_click_batch",
                return_value=send_click,
            ), mock.patch(
                "xar_autoplayer.control.executor.time.sleep"
            ):
                with self.assertRaisesRegex(AgentError, "committed finished WAL"):
                    driver.click_visible_control(token, timeout_seconds=1)
            self.assertEqual(
                [event["kind"] for event in events],
                ["ui_action_planned", "ui_input_armed", "ui_action_finished"],
            )
            receipt = json.loads(
                next(driver.artifacts.glob("*action*.json")).read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], "confirmed")
            self.assertEqual(receipt["send_input"]["accepted"], 2)
            self.assertNotIn("finished", receipt["durable_events"])

    def test_sendinput_exception_is_conservatively_possible_input(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-sendinput-error-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            fresh = observation("main_menu", (), spans=(target,))
            hover = observation("main_menu", (), spans=(target,))
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            self._prepare_window(window)
            window.capture_patch.side_effect = lambda bbox: hover_image.crop(bbox)
            driver.window = window
            fake_gui = types.SimpleNamespace(FAILSAFE=True, moveTo=mock.Mock())
            send_click = mock.Mock(
                side_effect=AgentError("SendInput failed after partial batch")
            )
            with mock.patch.object(
                driver, "_capture_observation", return_value=fresh
            ), mock.patch.object(
                driver,
                "_capture_observation_with_image",
                return_value=(hover, hover_image),
            ), mock.patch.dict(sys.modules, {"pyautogui": fake_gui}), mock.patch(
                "xar_autoplayer.control.executor._prepare_left_click_batch",
                return_value=send_click,
            ), mock.patch(
                "xar_autoplayer.control.executor.time.sleep"
            ):
                with self.assertRaisesRegex(AgentError, "partial batch"):
                    driver.click_visible_control(token, timeout_seconds=1)
            send_click.assert_called_once_with()
            receipt = json.loads(
                next(driver.artifacts.glob("*action*.json")).read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], "failed_after_possible_input")
            self.assertTrue(receipt["input_may_have_occurred"])


if __name__ == "__main__":
    unittest.main()
