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
    _choose_first_curse,
    _drive_opening,
    _extract_lifestyle_state,
    _extract_player_character_state,
    _score_first_blessing,
    _score_first_curse,
)
from xar_autoplayer.vision import load_ui_contract  # noqa: E402
from xar_autoplayer.vision.model import OcrSpan  # noqa: E402
from xar_autoplayer.vision.ocr import normalize_visible_text  # noqa: E402


def span(text: str, center: tuple[int, int], bbox: tuple[int, int, int, int]):
    return OcrSpan(text, normalize_visible_text(text), 0.95, center, bbox)


class OpeningContractTests(unittest.TestCase):
    def test_contract_exposes_opening_through_first_bargain_pair(self) -> None:
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
        map_spans = (
            span("暂停", (1280, 180), (1224, 149, 1337, 212)),
            span("政治地图", (2448, 1179), (2409, 1169, 2488, 1190)),
            span(
                "公元1066年9月15日",
                (2180, 1419),
                (2078, 1405, 2283, 1433),
            ),
        )
        self.assertEqual(contract.classify(map_spans, image)[0], "map_hud")
        character_spans = (
            map_spans[0],
            map_spans[1],
            map_spans[2],
            span("配偶", (431, 361), (409, 348, 453, 374)),
            span("玩家继承人", (688, 379), (640, 367, 736, 391)),
            span(
                "阿普利亚公爵，罗贝尔",
                (138, 432),
                (7, 419, 270, 445),
            ),
            span("这是你自己", (70, 465), (9, 454, 132, 477)),
        )
        self.assertEqual(
            contract.classify(character_spans, image)[0], "player_character"
        )
        self.assertEqual(
            contract.control("map_hud.open_player_character").click_point_px,
            (150, 1100),
        )
        lifestyle_selection_spans = (
            span("选择生活方式", (220, 45), (80, 20, 360, 70)),
            span("军事", (780, 610), (740, 590, 820, 630)),
            span("管理", (1120, 610), (1080, 590, 1160, 630)),
        )
        self.assertEqual(
            contract.classify(lifestyle_selection_spans, image)[0],
            "lifestyle_selection",
        )
        lifestyle_unfocused_spans = (
            span("军事生活方式", (190, 45), (80, 20, 300, 70)),
            span("生活方式重心", (350, 520), (270, 500, 430, 540)),
            span("当前：无重心", (350, 565), (270, 545, 430, 585)),
            span("权威重心", (350, 850), (300, 830, 400, 870)),
        )
        self.assertEqual(
            contract.classify(lifestyle_unfocused_spans, image)[0],
            "lifestyle_martial_unfocused",
        )
        lifestyle_authority_spans = (
            lifestyle_unfocused_spans[0],
            lifestyle_unfocused_spans[1],
            span("当前：权威重心", (350, 565), (260, 545, 440, 585)),
        )
        self.assertEqual(
            contract.classify(lifestyle_authority_spans, image)[0],
            "lifestyle_martial_authority",
        )
        self.assertEqual(
            contract.control("map_hud.open_lifestyle").click_point_px,
            (348, 1398),
        )

    def test_player_character_state_extracts_visible_family_baseline(self) -> None:
        state = _extract_player_character_state(
            {
                "screen": "player_character",
                "observation_id": "observation-player",
                "ocr": [
                    {"text": "阿普利亚公爵，罗贝尔"},
                    {"text": "这是你自己"},
                    {"text": "配偶"},
                    {"text": "玩家继承人"},
                    {"text": "亲族26"},
                    {"text": "廷臣 20"},
                    {"text": "臣属 7"},
                ],
            }
        )
        self.assertEqual(state["character"], "阿普利亚公爵，罗贝尔")
        self.assertTrue(state["spouse_visible"])
        self.assertTrue(state["player_heir_visible"])
        self.assertEqual(state["kin_count"], 26)
        self.assertEqual(state["courtier_count"], 20)
        self.assertEqual(state["vassal_count"], 7)

    def test_lifestyle_state_records_selected_authority_focus(self) -> None:
        state = _extract_lifestyle_state(
            {
                "screen": "lifestyle_martial_authority",
                "observation_id": "observation-focus",
                "ocr": [
                    {"text": "军事生活方式"},
                    {"text": "生活方式重心"},
                    {"text": "当前：权威重心"},
                ],
            }
        )
        self.assertEqual(state["lifestyle"], "军事")
        self.assertEqual(state["focus"], "权威")
        self.assertEqual(state["source_observation_id"], "observation-focus")

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

    def test_first_curse_strategy_avoids_long_health_penalty(self) -> None:
        choices = (
            (
                "curse_event.option_1",
                "普通-修正：蚀骨的寒痕（健康-0.4，持续10年)",
                988,
            ),
            (
                "curse_event.option_2",
                "普通-生活方式：烽火的湿薪（-1000军事经验）",
                1042,
            ),
        )
        controls = []
        spans = []
        for index, (control_id, text, y) in enumerate(choices):
            bbox = (730, y - 12, 1140, y + 12)
            controls.append(
                SimpleNamespace(
                    control_id=control_id,
                    token=f"curse-{index}",
                    bbox=bbox,
                    center=(935, y),
                )
            )
            spans.append(span(text, (935, y), bbox))
        selected, visible_text, loss = _choose_first_curse(
            SimpleNamespace(
                controls=tuple(controls),
                latest=SimpleNamespace(spans=tuple(spans)),
            )
        )
        self.assertEqual(selected.control_id, "curse_event.option_2")
        self.assertIn("军事经验", visible_text)
        self.assertEqual(loss, _score_first_curse(visible_text))

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
    def test_scenario_completes_first_pair_and_reaches_map(self) -> None:
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
                (
                    "curse_event.option_2",
                    "token-curse",
                    "map_hud",
                ),
                (
                    "map_hud.open_player_character",
                    "token-player",
                    "player_character",
                ),
                (
                    "map_hud.open_lifestyle",
                    "token-open-lifestyle",
                    "lifestyle_selection",
                ),
                (
                    "lifestyle_selection.open_martial",
                    "token-open-martial",
                    "lifestyle_martial_unfocused",
                ),
                (
                    "lifestyle_martial.select_authority_focus",
                    "token-authority",
                    "lifestyle_martial_authority",
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
                if control_id == "map_hud.open_player_character":
                    driver.click_visible_control.return_value["observation"]["ocr"] = [
                        {"text": "阿普利亚公爵，罗贝尔"},
                        {"text": "这是你自己"},
                        {"text": "配偶"},
                        {"text": "玩家继承人"},
                        {"text": "亲族26"},
                        {"text": "廷臣 20"},
                        {"text": "臣属 7"},
                    ]
                if control_id == "lifestyle_martial.select_authority_focus":
                    driver.click_visible_control.return_value["observation"]["ocr"] = [
                        {"text": "军事生活方式"},
                        {"text": "生活方式重心"},
                        {"text": "当前：权威重心"},
                    ]
                drivers.append(driver)
            escape_driver = mock.Mock()
            escape_driver.observe_stable.side_effect = (
                SimpleNamespace(
                    screen="player_character",
                    observation_id="obs-player-before-escape",
                ),
                SimpleNamespace(
                    screen="map_hud",
                    observation_id="obs-map-after-escape",
                ),
            )
            drivers.insert(8, escape_driver)
            blessing_driver = drivers[5]
            curse_driver = drivers[6]
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
            curse_choices = []
            curse_spans = []
            for index, (control_id, text, y) in enumerate(
                (
                    (
                        "curse_event.option_1",
                        "普通-修正：蚀骨的寒痕（健康-0.4，持续10年)",
                        988,
                    ),
                    (
                        "curse_event.option_2",
                        "普通-生活方式：烽火的湿薪（-1000军事经验）",
                        1042,
                    ),
                )
            ):
                bbox = (730, y - 12, 1140, y + 12)
                curse_choices.append(
                    SimpleNamespace(
                        control_id=control_id,
                        token=f"curse-choice-{index}",
                        bbox=bbox,
                        center=(935, y),
                    )
                )
                curse_spans.append(span(text, (935, y), bbox))
            curse_driver.observe_stable.return_value = SimpleNamespace(
                controls=tuple(curse_choices),
                latest=SimpleNamespace(spans=tuple(curse_spans)),
            )
            curse_driver.click_visible_control.return_value["action"][
                "control_id"
            ] = "curse_event.option_2"
            submit_key = mock.Mock(return_value=(2, 0))
            with mock.patch(
                "xar_autoplayer.vision.BoundGameWindow.bind_session",
                return_value=window,
            ), mock.patch(
                "xar_autoplayer.control.VisibleUiDriver", side_effect=drivers
            ) as driver_type, mock.patch(
                "xar_autoplayer.control.executor._prepare_key_press_batch",
                return_value=submit_key,
            ) as prepare_key:
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
            self.assertEqual(result["final_screen"], "lifestyle_martial_authority")
            self.assertEqual(
                [item["control_id"] for item in result["actions"]],
                [item[0] for item in controls[:8]]
                + ["player_character.close"]
                + [item[0] for item in controls[8:]],
            )
            self.assertEqual(driver_type.call_count, 12)
            for driver, (_, token, _) in zip(drivers[:5], controls[:5]):
                driver.click_visible_control.assert_called_once()
                self.assertEqual(
                    driver.click_visible_control.call_args.args[0], token
                )
            blessing_driver.click_visible_control.assert_called_once_with(
                "choice-0",
                timeout_seconds=mock.ANY,
            )
            curse_driver.click_visible_control.assert_called_once_with(
                "curse-choice-1",
                timeout_seconds=mock.ANY,
            )
            drivers[7].click_visible_control.assert_called_once_with(
                "token-player",
                timeout_seconds=mock.ANY,
            )
            prepare_key.assert_called_once_with(0x3B)
            submit_key.assert_called_once_with()
            self.assertIn("长明的定力", result["first_blessing_choice"]["visible_text"])
            self.assertIn("军事经验", result["first_curse_choice"]["visible_text"])
            self.assertTrue(result["player_character_state"]["spouse_visible"])
            self.assertTrue(result["player_character_state"]["player_heir_visible"])
            self.assertEqual(result["lifestyle_state"]["focus"], "权威")

    def test_cli_exposes_opening_smoke(self) -> None:
        args = cli.parser().parse_args(["opening-smoke"])
        self.assertEqual(args.command, "opening-smoke")
        self.assertEqual(args.timeout, 300)


if __name__ == "__main__":
    unittest.main()
