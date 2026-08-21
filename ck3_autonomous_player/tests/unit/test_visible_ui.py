from __future__ import annotations

import json
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
)
from xar_autoplayer.vision.model import (  # noqa: E402
    Observation,
    OcrSpan,
    VisibleAnchor,
    VisibleControl,
)
from xar_autoplayer.vision.ocr import normalize_visible_text  # noqa: E402


UI_CONTRACT = (
    ROOT / "configs" / "ui" / "ck3-1.19.0.6.zh-hans.2560x1440.json"
)


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
) -> Observation:
    return Observation(
        observation_id="1" * 32,
        frame_id="2" * 32,
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
    )


class UiClassifierTests(unittest.TestCase):
    def test_main_menu_requires_three_distinct_visible_spans(self) -> None:
        contract = load_ui_contract(UI_CONTRACT)
        spans = (
            span("继续游戏", (599, 477), (548, 463, 652, 491), 0.80),
            span("新游戏", (600, 557), (560, 543, 640, 571), 0.75),
            span("载入游戏", (600, 637), (548, 624, 652, 650), 0.76),
        )
        screen, confidence, reasons, anchors = contract.classify(spans)
        self.assertEqual(screen, "main_menu")
        self.assertEqual(reasons, ())
        self.assertEqual(len(anchors), 3)
        self.assertAlmostEqual(confidence, 0.77, places=2)

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
                span("开始教程", (1270, 820), (1200, 800, 1340, 840)),
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
        self.assertEqual(contract.classify(spans)[0], "bookmark_lobby")

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


class UiDriverSafetyTests(unittest.TestCase):
    def _driver(self, root: Path) -> tuple[VisibleUiDriver, ControlSpec, OcrSpan, str]:
        artifacts = root / "state" / "runs" / "run-1" / "artifacts"
        artifacts.mkdir(parents=True)
        driver = object.__new__(VisibleUiDriver)
        driver.artifacts = artifacts
        driver.events = artifacts.parent / "ui-events.jsonl"
        driver._sequence = 0
        driver._issued = {}
        driver._session_nonce = "session"
        driver._secret = b"secret"
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
        )
        driver._issued[token] = _IssuedControl(before, spec, target, time.monotonic())
        return driver, spec, target, token

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
        )
        moved = observation(
            "bookmark_lobby",
            (VisibleAnchor("lobby.title", "title", 0.9, (30, 0, 40, 10), (35, 5)),),
        )
        stable = observation(
            "bookmark_lobby",
            (VisibleAnchor("lobby.title", "title", 0.9, (31, 0, 41, 10), (36, 5)),),
        )
        with mock.patch.object(
            driver, "_capture_observation", side_effect=[first, moved, stable]
        ), mock.patch("xar_autoplayer.control.executor.time.sleep"):
            result = driver.observe_stable("bookmark_lobby", 2, stable_frames=2)
        self.assertIs(result, stable)

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
            window.client_rect = (0, 0, 2560, 1440)
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
            self.assertEqual(receipt["status"], "rejected_before_input")
            self.assertFalse(receipt["input_may_have_occurred"])

    def test_token_expiring_during_final_guards_causes_zero_input(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-final-expiry-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            issued_at = driver._issued[token].issued_monotonic
            fresh = observation("main_menu", (), spans=(target,))
            hover = observation("main_menu", (), spans=(target,))
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            window.client_rect = (0, 0, 2560, 1440)
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
            self.assertEqual(receipt["status"], "rejected_before_input")
            self.assertFalse(receipt["input_may_have_occurred"])

    def test_focus_or_overlay_change_after_hover_causes_zero_mouse_down(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-hover-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            fresh = observation("main_menu", (), spans=(target,))
            hover = observation("main_menu", (), spans=(target,))
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            window.client_rect = (0, 0, 2560, 1440)
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
            receipt = json.loads(next(driver.artifacts.glob("*action*.json")).read_text())
            self.assertEqual(receipt["status"], "rejected_before_input")
            self.assertFalse(receipt["input_may_have_occurred"])

    def test_postcondition_failure_keeps_durable_possible_input_receipt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-receipt-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            fresh = observation("main_menu", (), spans=(target,))
            hover = observation("main_menu", (), spans=(target,))
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            window.client_rect = (0, 0, 2560, 1440)
            window.capture_patch.side_effect = lambda bbox: hover_image.crop(bbox)
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
            receipt = json.loads(next(driver.artifacts.glob("*action*.json")).read_text())
            self.assertEqual(receipt["status"], "failed_after_possible_input")
            self.assertTrue(receipt["input_may_have_occurred"])
            event_kinds = [
                json.loads(line)["kind"]
                for line in driver.events.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                event_kinds,
                ["ui_action_planned", "ui_input_attempting", "ui_action_finished"],
            )

    def test_target_patch_replacement_after_attempt_receipt_causes_zero_input(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-patch-change-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            fresh = observation("main_menu", (), spans=(target,))
            hover = observation("main_menu", (), spans=(target,))
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            window.client_rect = (0, 0, 2560, 1440)

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
                event_kinds = [
                    json.loads(line)["kind"]
                    for line in driver.events.read_text(encoding="utf-8").splitlines()
                ]
                self.assertEqual(
                    event_kinds, ["ui_action_planned", "ui_input_attempting"]
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
            self.assertEqual(receipt["status"], "rejected_before_input")
            self.assertFalse(receipt["input_may_have_occurred"])

    def test_final_cursor_guard_failure_after_patch_causes_zero_input(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-final-guard-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            fresh = observation("main_menu", (), spans=(target,))
            hover = observation("main_menu", (), spans=(target,))
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            window.client_rect = (0, 0, 2560, 1440)
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

    def test_sendinput_exception_is_conservatively_possible_input(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ui-sendinput-error-") as temporary:
            driver, _spec, target, token = self._driver(Path(temporary))
            fresh = observation("main_menu", (), spans=(target,))
            hover = observation("main_menu", (), spans=(target,))
            hover_image = Image.new("RGB", (2560, 1440), "black")
            window = mock.Mock()
            window.client_rect = (0, 0, 2560, 1440)
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
