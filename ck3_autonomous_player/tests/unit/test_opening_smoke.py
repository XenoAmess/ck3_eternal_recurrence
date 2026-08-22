from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer import cli  # noqa: E402
from xar_autoplayer.control import VisibleUiDriver  # noqa: E402
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.opening_smoke import (  # noqa: E402
    OPENING_ALLOWED_CONTROLS,
    OPENING_CONTRACT,
    _choose_first_blessing,
    _drive_opening,
    _score_first_blessing,
)
from xar_autoplayer.vision import load_ui_contract  # noqa: E402
from xar_autoplayer.vision.model import OcrSpan  # noqa: E402
from xar_autoplayer.vision.ocr import normalize_visible_text  # noqa: E402


def span(text: str, center: tuple[int, int], bbox: tuple[int, int, int, int]):
    return OcrSpan(text, normalize_visible_text(text), 0.95, center, bbox)


class OpeningContractTests(unittest.TestCase):
    def test_contract_exposes_opening_through_first_blessing_choice(self) -> None:
        digest = hashlib.sha256(OPENING_CONTRACT.read_bytes()).hexdigest()
        contract = load_ui_contract(OPENING_CONTRACT, expected_sha256=digest)
        self.assertEqual(
            frozenset(item.control_id for item in contract.controls),
            OPENING_ALLOWED_CONTROLS,
        )
        self.assertEqual(
            contract.control("bookmark_lobby.select_robert").hover_tolerance_px,
            10,
        )
        self.assertEqual(
            contract.control("bookmark_lobby.select_robert").click_offset_px,
            (0, -130),
        )
        self.assertEqual(
            contract.control("bookmark_lobby.select_robert").click_hold_seconds,
            0.12,
        )
        self.assertTrue(
            contract.control("bookmark_lobby.select_robert").allow_dynamic_pixels
        )
        self.assertEqual(
            contract.control("bookmark_lobby.start_game").hover_tolerance_px,
            3,
        )
        self.assertEqual(
            contract.control("bookmark_lobby.start_game").click_offset_px,
            (0, 0),
        )
        self.assertTrue(
            contract.control("bookmark_lobby.start_game").allow_dynamic_pixels
        )
        self.assertTrue(
            contract.control("pact_event.accept_contract").allow_dynamic_pixels
        )
        self.assertTrue(
            contract.control("first_life_event.begin").allow_dynamic_pixels
        )
        lobby_image = Image.new("RGB", contract.resolution, (0, 0, 0))
        lobby = next(
            item for item in contract.screens if item.screen_id == "bookmark_lobby"
        )
        for probe in lobby.pixel_probes:
            colour = tuple(
                round((minimum + maximum) / 2)
                for minimum, maximum in zip(
                    probe.mean_rgb_min, probe.mean_rgb_max
                )
            )
            lobby_image.paste(colour, probe.rect)
        lobby_spans = (
            span("选择初始日期和角色", (500, 50), (400, 30, 600, 70)),
            span(
                "公爵弗拉季斯拉夫",
                (1400, 450),
                (1300, 420, 1500, 480),
            ),
            span("公爵罗贝尔", (1561, 1200), (1491, 1187, 1632, 1220)),
        )
        self.assertEqual(
            contract.classify(lobby_spans, lobby_image)[0], "bookmark_lobby"
        )
        self.assertEqual(
            contract.classify(
                (
                    lobby_spans[0],
                    lobby_spans[1],
                    span(
                        "公爵罗贝尔，51岁",
                        (2260, 590),
                        (2139, 575, 2381, 605),
                    ),
                    span("开始", (2260, 1267), (2227, 1248, 2294, 1286)),
                ),
                lobby_image,
            )[0],
            "bookmark_lobby_selected",
        )
        image = Image.new("RGB", contract.resolution, (0, 0, 0))
        pact_spans = (
            span("终末之契", (792, 401), (715, 378, 870, 424)),
            span("又见面了，旅人。", (733, 471), (659, 460, 807, 483)),
        )
        self.assertEqual(contract.classify(pact_spans, image)[0], "pact_event")
        first_life_spans = (
            span("未燃之世", (793, 401), (716, 379, 870, 423)),
            span("那么，开始此生。", (930, 1042), (850, 1031, 1010, 1054)),
        )
        self.assertEqual(
            contract.classify(first_life_spans, image)[0], "first_life_event"
        )
        blessing_spans = (
            span("琉焰的垂青", (810, 401), (718, 381, 902, 421)),
            span(
                "只是规矩你懂：每一份垂青，都要用一道咒痕来换。",
                (897, 557),
                (622, 543, 1173, 571),
            ),
        )
        self.assertEqual(
            contract.classify(blessing_spans, image)[0], "blessing_event"
        )
        curse_spans = (
            span("等价的咒痕", (810, 401), (718, 381, 902, 421)),
            span("挑好了？那么——该付账了。", (760, 471), (622, 459, 900, 483)),
        )
        self.assertEqual(contract.classify(curse_spans, image)[0], "curse_event")

    def test_first_blessing_strategy_prefers_permanent_trait(self) -> None:
        choices = (
            ("blessing_event.option_1", "普通-特质：长明的定力 (耐心)", 879),
            ("blessing_event.option_2", "普通-属性：权衡（+1管理）", 934),
            (
                "blessing_event.option_3",
                "普通-生活方式：智海的拾贝（+750学识经验）",
                989,
            ),
        )
        controls = []
        spans = []
        for index, (control_id, text, y) in enumerate(choices):
            bbox = (750, y - 12, 1120, y + 12)
            controls.append(
                SimpleNamespace(
                    control_id=control_id,
                    token=f"token-{index}",
                    bbox=bbox,
                    center=(935, y),
                )
            )
            spans.append(span(text, (935, y), bbox))
        selected, visible_text, score = _choose_first_blessing(
            SimpleNamespace(
                controls=tuple(controls),
                latest=SimpleNamespace(spans=tuple(spans)),
            )
        )
        self.assertEqual(selected.control_id, "blessing_event.option_1")
        self.assertIn("长明的定力", visible_text)
        self.assertEqual(score, _score_first_blessing(visible_text))

    def test_explicit_opening_allowlist_does_not_change_default_driver_policy(
        self,
    ) -> None:
        digest = hashlib.sha256(OPENING_CONTRACT.read_bytes()).hexdigest()
        contract = load_ui_contract(OPENING_CONTRACT, expected_sha256=digest)
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary) / "state" / "runs" / "run" / "artifacts"
            artifacts.mkdir(parents=True)
            driver = VisibleUiDriver(
                mock.Mock(),
                contract,
                artifacts,
                expected_game_version="1.19.0.6",
                expected_language="l_simp_chinese",
                expected_contract_sha256=digest,
                durable_event_callback=lambda _event: "a" * 64,
                allowed_controls=OPENING_ALLOWED_CONTROLS,
            )
            self.assertEqual(driver.registered_capabilities, OPENING_ALLOWED_CONTROLS)
            with self.assertRaisesRegex(AgentError, "allowlist differs"):
                VisibleUiDriver(
                    mock.Mock(),
                    contract,
                    artifacts,
                    expected_game_version="1.19.0.6",
                    expected_language="l_simp_chinese",
                    expected_contract_sha256=digest,
                    durable_event_callback=lambda _event: "a" * 64,
                    allowed_controls=frozenset({"main_menu.new_game"}),
                )


class OpeningScenarioTests(unittest.TestCase):
    def test_scenario_chooses_first_blessing_and_reaches_curse(self) -> None:
        digest = hashlib.sha256(OPENING_CONTRACT.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "state" / "runs" / "run"
            artifacts = root / "artifacts"
            artifacts.mkdir(parents=True)
            contract = root / "opening-ui-contract.json"
            contract.write_bytes(OPENING_CONTRACT.read_bytes())
            events = root / "events.jsonl"
            window = mock.Mock(pid=10, hwnd=20)
            window.request_foreground_without_input.return_value = {
                "status": "confirmed"
            }
            window.audit_binding.return_value = {"process": {"pid": 10}}
            handle = SimpleNamespace(
                process=mock.Mock(poll=mock.Mock(return_value=None))
            )
            controls = (
                ("main_menu.new_game", "token-new", "bookmark_lobby"),
                (
                    "bookmark_lobby.select_robert",
                    "token-robert",
                    "bookmark_lobby_selected",
                ),
                ("bookmark_lobby.start_game", "token-start", "pact_event"),
                (
                    "pact_event.accept_contract",
                    "token-accept",
                    "first_life_event",
                ),
                (
                    "first_life_event.begin",
                    "token-begin",
                    "blessing_event",
                ),
                (
                    "blessing_event.option_1",
                    "token-blessing",
                    "curse_event",
                ),
            )
            drivers = []
            for index, (control_id, token, post_screen) in enumerate(controls):
                driver = mock.Mock()
                visible_text = (
                    "普通-特质：长明的定力 (耐心)"
                    if control_id == "blessing_event.option_1"
                    else control_id
                )
                bbox = (800, 860, 1080, 890)
                visible_control = SimpleNamespace(
                    control_id=control_id,
                    token=token,
                    bbox=bbox,
                    center=(940, 875),
                )
                driver.observe_stable.return_value = SimpleNamespace(
                    controls=(visible_control,),
                    latest=SimpleNamespace(
                        spans=(span(visible_text, (940, 875), bbox),)
                    ),
                )
                driver.click_visible_control.return_value = {
                    "action": {
                        "control_id": control_id,
                        "status": "confirmed",
                        "receipt_artifact": f"artifacts/action-{index}.json",
                        "send_input": {
                            "requested": 2,
                            "accepted": 2,
                            "last_error": 0,
                        },
                        "result_observation_id": f"obs-{index}",
                        "expected_post_screen": post_screen,
                    },
                    "observation": {
                        "screen": post_screen,
                        "observation_id": f"obs-{index}",
                    },
                }
                drivers.append(driver)
            blessing_driver = drivers[-1]
            blessing_choices = []
            blessing_spans = []
            for index, (control_id, text, y) in enumerate(
                (
                    (
                        "blessing_event.option_1",
                        "普通-特质：长明的定力 (耐心)",
                        879,
                    ),
                    (
                        "blessing_event.option_2",
                        "普通-属性：权衡（+1管理）",
                        934,
                    ),
                    (
                        "blessing_event.option_3",
                        "普通-生活方式：智海的拾贝（+750学识经验）",
                        989,
                    ),
                )
            ):
                bbox = (740, y - 12, 1130, y + 12)
                blessing_choices.append(
                    SimpleNamespace(
                        control_id=control_id,
                        token=f"choice-{index}",
                        bbox=bbox,
                        center=(935, y),
                    )
                )
                blessing_spans.append(span(text, (935, y), bbox))
            blessing_driver.observe_stable.return_value = SimpleNamespace(
                controls=tuple(blessing_choices),
                latest=SimpleNamespace(spans=tuple(blessing_spans)),
            )
            blessing_driver.click_visible_control.return_value["action"][
                "control_id"
            ] = "blessing_event.option_1"
            with mock.patch(
                "xar_autoplayer.vision.BoundGameWindow.bind_session",
                return_value=window,
            ), mock.patch(
                "xar_autoplayer.control.VisibleUiDriver", side_effect=drivers
            ) as driver_type:
                result = _drive_opening(
                    SimpleNamespace(
                        game_exe=Path("ck3.exe"),
                        expected_game_version="1.19.0.6",
                    ),
                    handle,
                    {"display": {"language": "l_simp_chinese"}},
                    artifacts,
                    events,
                    contract,
                    digest,
                    time.monotonic() + 30,
                )
            self.assertEqual(result["final_screen"], "curse_event")
            self.assertEqual(
                [item["control_id"] for item in result["actions"]],
                [item[0] for item in controls],
            )
            self.assertEqual(driver_type.call_count, 6)
            for driver, (_, token, _) in zip(drivers[:-1], controls[:-1]):
                driver.click_visible_control.assert_called_once()
                self.assertEqual(
                    driver.click_visible_control.call_args.args[0], token
                )
            blessing_driver.click_visible_control.assert_called_once_with(
                "choice-0",
                timeout_seconds=mock.ANY,
            )
            self.assertIn("长明的定力", result["first_blessing_choice"]["visible_text"])

    def test_cli_exposes_opening_smoke(self) -> None:
        args = cli.parser().parse_args(["opening-smoke"])
        self.assertEqual(args.command, "opening-smoke")
        self.assertEqual(args.timeout, 300)


if __name__ == "__main__":
    unittest.main()
