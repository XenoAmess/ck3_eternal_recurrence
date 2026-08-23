from __future__ import annotations

import hashlib
import json
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
    ACTIVE_EVENT_PREVIEW_REGION,
    INITIAL_MAIN_MENU_TIMEOUT_SECONDS,
    INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    MAP_PANEL_SHORTCUTS,
    OPENING_ALLOWED_CONTROLS,
    OPENING_CONTRACT,
    OPENING_DEVELOPMENT_STEPS,
    ROBERT_DEVELOPMENT_COUNTY_CANDIDATE_POINTS,
    STEWARD_DEVELOP_COUNTY_TASK_CENTER,
    _building_construction_in_progress,
    _county_label_target_candidates,
    _choose_first_blessing,
    _choose_first_curse,
    _choose_economic_building_offer,
    _building_offer_summaries,
    _call_to_war_in_frame,
    _choose_generic_event_option,
    _confirm_post_shortcut_event,
    _drive_opening,
    _extract_map_date,
    _extract_lifestyle_state,
    _extract_player_character_state,
    _extract_current_life_succession_state,
    _extract_death_terminal,
    _child_portrait_candidates,
    _death_terminal_state,
    _marriage_acceptance_in_frame,
    _generic_event_in_frame,
    _visible_event_preview,
    _panel_summary,
    _choose_one_life_dynasty_action,
    _palermo_map_targets,
    _pause_menu_visible,
    _save_window_visible,
    _same_generic_event,
    _score_first_blessing,
    _score_first_curse,
    _score_generic_event_option,
    _spans_with_text,
    _steward_development_active,
    _steward_development_assignment_confirmation,
    _steward_development_targeting_active,
    replay_opening_observation,
)
from xar_autoplayer.strategy import (  # noqa: E402
    choose_one_life_turn,
    read_one_life_strategy,
    record_one_life_episode,
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
        running_spans = (
            map_spans[1],
            span(
                "公元1067年1月2日",
                (2180, 1419),
                (2078, 1405, 2283, 1433),
            ),
        )
        self.assertEqual(contract.classify(running_spans, image)[0], "map_running")
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
            contract.classify(character_spans[:-1], image)[0], "player_character"
        )
        self.assertEqual(
            contract.control("map_hud.open_player_character").click_point_px,
            (150, 1100),
        )
        lifestyle_selection_spans = (
            span("选择生活方式", (1281, 47), (1192, 30, 1370, 64)),
            span("军事", (877, 387), (842, 367, 913, 407)),
            span("管理", (1243, 387), (1208, 367, 1279, 408)),
        )
        self.assertEqual(
            contract.classify(lifestyle_selection_spans, image)[0],
            "lifestyle_selection",
        )
        lifestyle_unfocused_spans = (
            span("军事生活方式", (192, 78), (60, 57, 325, 100)),
            span("生活方式重心", (559, 296), (501, 284, 617, 308)),
            span("当前：无重心", (558, 340), (500, 328, 617, 352)),
            span("权威重心", (478, 720), (430, 706, 526, 734)),
        )
        self.assertEqual(
            contract.classify(lifestyle_unfocused_spans, image)[0],
            "lifestyle_martial_unfocused",
        )
        lifestyle_confirmation_spans = lifestyle_unfocused_spans + (
            span("选择权威重心", (1280, 453), (1191, 435, 1369, 471)),
            span("取消", (1143, 985), (1121, 972, 1166, 998)),
            span("选择", (1420, 985), (1397, 972, 1442, 998)),
        )
        self.assertEqual(
            contract.classify(lifestyle_confirmation_spans, image)[0],
            "lifestyle_authority_confirmation",
        )
        lifestyle_authority_spans = (
            lifestyle_unfocused_spans[0],
            lifestyle_unfocused_spans[1],
            span("当前：权威重心", (575, 340), (500, 328, 650, 352)),
        )
        self.assertEqual(
            contract.classify(lifestyle_authority_spans, image)[0],
            "lifestyle_martial_authority",
        )
        self.assertEqual(
            contract.control("map_hud.open_lifestyle").click_point_px,
            (348, 1398),
        )
        self.assertEqual(
            contract.control("lifestyle_martial_authority.close").click_point_px,
            (2465, 79),
        )
        self.assertEqual(
            contract.control("map_hud.set_speed_five").click_point_px,
            (2536, 1418),
        )
        self.assertEqual(
            contract.control("lifestyle_martial.select_authority_focus").post_screen,
            "lifestyle_authority_confirmation",
        )

    def test_player_character_state_extracts_visible_family_baseline(self) -> None:
        state = _extract_player_character_state(
            {
                "screen": "player_character",
                "observation_id": "observation-player",
                "ocr": [
                    {"text": "阿普利亚公爵，罗贝尔"},
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
        self.assertEqual(state["child_count"], None)
        self.assertEqual(state["kin_count"], 26)
        self.assertEqual(state["courtier_count"], 20)
        self.assertEqual(state["vassal_count"], 7)

    def test_one_life_dynasty_strategy_never_continues_as_heir(self) -> None:
        stable = _choose_one_life_dynasty_action(
            {
                "spouse_visible": True,
                "player_heir_visible": True,
                "child_count": 7,
            }
        )
        self.assertEqual(
            stable["action"], "hold_player_marriage_review_child_alliances_later"
        )
        self.assertFalse(stable["continue_as_heir_after_death"])
        self.assertEqual(
            _choose_one_life_dynasty_action(
                {"spouse_visible": False, "player_heir_visible": True}
            )["action"],
            "seek_player_spouse",
        )

    def test_succession_state_is_current_life_only(self) -> None:
        frame = SimpleNamespace(
            observation_id="succession-observation",
            spans=(
                span("继承", (100, 100), (50, 80, 150, 120)),
                span("玩家继承人", (200, 200), (150, 180, 250, 220)),
                span("分割继承制", (300, 300), (250, 280, 350, 320)),
                span("你将失去2个头衔", (400, 400), (320, 380, 480, 420)),
            ),
        )
        state = _extract_current_life_succession_state(frame)
        self.assertTrue(state["player_heir_visible"])
        self.assertTrue(state["partition_risk_visible"])
        self.assertTrue(state["strategy"]["death_is_terminal_settlement"])
        self.assertFalse(state["strategy"]["continue_as_heir_after_death"])

    def test_child_portrait_candidates_follow_native_seven_slot_grid(self) -> None:
        frame = SimpleNamespace(
            spans=(span("子女（7)", (46, 1146), (12, 1134, 81, 1158)),)
        )
        self.assertEqual(
            _child_portrait_candidates(frame),
            tuple((45 + 85 * index, 1210) for index in range(7)),
        )

    def test_marriage_acceptance_is_current_life_value(self) -> None:
        frame = SimpleNamespace(
            observation_id="marriage-response",
            spans=(
                span("我很乐意接受你的订婚提议！", (100, 100), (0, 80, 200, 120)),
                span("你的女儿埃玛将与我的儿子贝内迪克特订婚。", (200, 200), (0, 180, 400, 220)),
                span("太好了！", (300, 300), (250, 280, 350, 320)),
            ),
        )
        result = _marriage_acceptance_in_frame(frame)
        self.assertEqual(result["status"], "accepted_betrothal")
        self.assertFalse(result["continue_as_heir_after_death"])

    def test_call_to_war_detector_reads_diplomatic_letter_layout(self) -> None:
        frame = SimpleNamespace(
            observation_id="call-to-war",
            client_rect=(0, 0, 2560, 1440),
            spans=(
                span("召集加入战争", (1264, 177), (1176, 161, 1352, 194)),
                span(
                    "我要求你尊重我们的同盟并与我加入丹麦声索挪威王国战争！",
                    (1280, 410),
                    (1000, 390, 1560, 430),
                ),
                span("拒绝", (1160, 1167), (1138, 1154, 1183, 1180)),
                span("同意", (1401, 1167), (1379, 1154, 1423, 1181)),
            ),
        )
        result = _call_to_war_in_frame(frame)
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "alliance_call_visible")
        self.assertIn("丹麦", result["war_text"])

    def test_death_terminal_distinguishes_handoff_and_settlement(self) -> None:
        succession = SimpleNamespace(
            observation_id="death-succession",
            spans=(
                span("你已过世", (1280, 200), (1150, 170, 1410, 230)),
                span("继续扮演", (1500, 1120), (1400, 1090, 1600, 1150)),
            ),
        )
        self.assertEqual(
            _death_terminal_state(succession), "native_succession_handoff"
        )

        settlement = SimpleNamespace(
            observation_id="death-settlement",
            spans=(
                span("轮回终结", (330, 150), (260, 125, 420, 175)),
                span(
                    "辛苦了，旅人。这一生的分量，我已仔细称过。",
                    (500, 220),
                    (170, 205, 830, 235),
                ),
                span("最终分数：123.5", (420, 650), (200, 630, 640, 670)),
                span("此前纪录：100", (400, 690), (200, 670, 600, 710)),
                span("差值：+23.5", (380, 730), (200, 710, 560, 750)),
                span("很好。这笔账，已记入永恒。", (500, 800), (300, 780, 700, 820)),
            ),
        )
        result = _extract_death_terminal(settlement)
        self.assertEqual(result["terminal_kind"], "recurrence_settlement_event")
        self.assertEqual(result["score"]["final"], 123.5)
        self.assertEqual(result["score"]["previous_record"], 100)
        self.assertEqual(result["score"]["delta"], 23.5)
        self.assertFalse(result["continue_as_heir_after_death"])

    def test_native_no_heir_settlement_reads_separate_score_column(self) -> None:
        frame = SimpleNamespace(
            observation_id="no-heir-settlement",
            spans=(
                span("轮回终结", (1280, 220), (1190, 195, 1370, 245)),
                span("最终分量", (660, 330), (590, 310, 730, 350)),
                span("42.5", (1440, 330), (1400, 310, 1480, 350)),
                span("完成交易", (660, 390), (590, 370, 730, 410)),
                span("3", (1440, 390), (1420, 370, 1460, 410)),
                span("退出到菜单", (1280, 930), (1120, 900, 1440, 960)),
            ),
        )
        result = _extract_death_terminal(frame)
        self.assertEqual(result["terminal_kind"], "native_no_heir_settlement")
        self.assertEqual(result["score"]["final"], 42.5)
        self.assertEqual(result["score"]["completed_bargains"], 3)

    def test_cross_run_strategy_records_one_life_outcomes(self) -> None:
        commands = [
            {
                "command": "war-enforce-demands",
                "ok": True,
                "result": {"war_victory": {"status": "victory_enforced"}},
            },
            {
                "command": "war-disband-armies",
                "ok": True,
                "result": {"army_disband": {"status": "disbanded"}},
            },
            {
                "command": "succession-review",
                "ok": True,
                "result": {
                    "succession_state": {"partition_risk_visible": True}
                },
            },
            {
                "command": "marriage-confirm-response",
                "ok": True,
                "result": {
                    "marriage_result": {"status": "accepted_betrothal"}
                },
            },
            {
                "command": "save-checkpoint",
                "ok": True,
                "result": {
                    "checkpoint": {
                        "name": "life.ck3",
                        "size": 10,
                        "sha256": "a" * 64,
                    }
                },
            },
        ]
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary)
            recorded = record_one_life_episode(
                state,
                run_id="run-one",
                commands=commands,
                terminal={
                    "terminal": True,
                    "technical_settlement_handoff": True,
                    "score": {"final": 123.5},
                },
            )
            episode = recorded["recorded_episode"]
            self.assertTrue(episode["achievements"]["palermo_holy_war_won"])
            self.assertTrue(episode["achievements"]["danish_betrothal_accepted"])
            self.assertEqual(episode["heir_gameplay_actions"], 0)
            self.assertFalse(recorded["continue_as_heir_after_death"])
            reread = read_one_life_strategy(state)
            self.assertEqual(len(reread["episodes"]), 1)
            self.assertEqual(
                reread["next_run_plan"]["priorities"][0]["action"],
                "repeat_palermo_opening_war_when_visible_conditions_match",
            )

    def test_one_life_turn_planner_advances_milestones_and_interruptions(
        self,
    ) -> None:
        commands: list[dict[str, object]] = []

        def selected() -> str:
            return str(choose_one_life_turn(commands)["selected_step"])

        def success(command: str, result: dict[str, object] | None = None) -> None:
            commands.append(
                {
                    "index": len(commands) + 1,
                    "command": command,
                    "ok": True,
                    "result": result or {},
                }
            )

        self.assertEqual(selected(), "save-checkpoint")
        success("save-checkpoint")
        self.assertEqual(selected(), "dynasty-review")
        success("dynasty-review")
        self.assertEqual(selected(), "succession-review")
        success("succession-review")
        self.assertEqual(selected(), "marriage-review")
        success("marriage-review")
        self.assertEqual(selected(), "marriage-alliance")
        success("marriage-alliance")
        self.assertEqual(selected(), "marriage-confirm-response")
        commands.append(
            {
                "index": len(commands) + 1,
                "command": "marriage-confirm-response",
                "ok": False,
                "error": "AgentError: accepted marriage response is not visibly stable",
            }
        )
        self.assertEqual(selected(), "war-advance-week")
        success("war-advance-week")
        self.assertEqual(selected(), "marriage-confirm-response")
        success("marriage-confirm-response")
        self.assertEqual(selected(), "war-declare-palermo")
        success("war-declare-palermo")
        self.assertEqual(selected(), "war-raise-all")
        success("war-raise-all")
        self.assertEqual(selected(), "war-siege-palermo")
        success("war-siege-palermo")
        self.assertEqual(selected(), "war-status")
        success("war-status", {"war_status": {"war_score_percent": 0}})
        self.assertEqual(selected(), "war-advance-week")
        success("war-advance-week")
        self.assertEqual(selected(), "war-status")
        success("war-status", {"war_status": {"war_score_percent": 100}})
        self.assertEqual(selected(), "war-enforce-demands")
        success("war-enforce-demands")
        self.assertEqual(selected(), "war-disband-armies")
        success("war-disband-armies")
        self.assertEqual(selected(), "save-checkpoint")
        success("save-checkpoint")
        self.assertEqual(selected(), "life-advance")
        success("life-advance")
        success("life-advance")
        success("life-advance")
        self.assertEqual(selected(), "save-checkpoint")

        commands.append(
            {
                "index": len(commands) + 1,
                "command": "auto-turn",
                "ok": False,
                "error": "AgentError: ordinary event interrupted war advance",
            }
        )
        self.assertEqual(selected(), "resolve-current-event")

        commands.append(
            {
                "index": len(commands) + 1,
                "command": "auto-turn",
                "ok": False,
                "error": (
                    "AgentError: one-life death terminal visible: "
                    "native_succession_handoff"
                ),
            }
        )
        self.assertEqual(selected(), "death-terminal")

        success("death-terminal")
        self.assertEqual(selected(), "strategy-review")

    def test_palermo_target_comes_from_visible_map_label(self) -> None:
        frame = SimpleNamespace(
            client_rect=(0, 0, 2560, 1440),
            spans=(
                span("辉莱尔", (672, 1261), (580, 1203, 765, 1319)),
                span("萨莱诺", (1191, 643), (1092, 566, 1291, 721)),
            ),
        )
        self.assertEqual(_palermo_map_targets(frame), ((672, 1261),))

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

    def test_map_date_extracts_visible_progress(self) -> None:
        state = _extract_map_date(
            {
                "screen": "map_running",
                "observation_id": "observation-date",
                "ocr": [
                    {
                        "text": "当前日期：1066年9月18日",
                        "bbox": [2023, 1222, 2303, 1248],
                    },
                    {
                        "text": "开始：1066年9月15日",
                        "bbox": [2022, 1259, 2215, 1282],
                    },
                    {
                        "text": "公元 1066 年 9 月 18 日",
                        "bbox": [2079, 1407, 2285, 1433],
                    },
                ],
            }
        )
        self.assertEqual((state["year"], state["month"], state["day"]), (1066, 9, 18))
        self.assertEqual(state["source_observation_id"], "observation-date")

    def test_generic_event_detector_finds_stable_native_option_lane(self) -> None:
        def observation(sequence: int, y_offset: int = 0):
            return SimpleNamespace(
                observation_id=f"event-{sequence}",
                capture_sequence=sequence,
                client_rect=(0, 0, 2560, 1440),
                spans=(
                    span("怀孕！", (764, 402 + y_offset), (717, 380, 812, 424)),
                    span(
                        "命运对我微笑！我的妻子怀上了我的孩子。",
                        (904, 470),
                        (624, 459, 1185, 482),
                    ),
                    span(
                        "我等不及要将小婴儿抱在怀里了！",
                        (932, 1043 + y_offset),
                        (794, 1032, 1070, 1055),
                    ),
                    span("政治地图", (2449, 1180), (2409, 1168, 2490, 1192)),
                ),
            )

        first = _generic_event_in_frame(observation(7))
        second = _generic_event_in_frame(observation(8, 2))
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertTrue(_same_generic_event(first, second))
        self.assertEqual(first["title"], "怀孕！")
        self.assertEqual(first["options"][0]["option_number"], 1)
        self.assertIn("小婴儿", first["options"][0]["visible_text"])

        faded = observation(9)
        gone = SimpleNamespace(
            observation_id="map-after-event",
            capture_sequence=10,
            client_rect=(0, 0, 2560, 1440),
            spans=(
                span("政治地图", (2449, 1180), (2409, 1168, 2490, 1192)),
                span("公元1067年1月16日", (2181, 1420), (2077, 1407, 2285, 1433)),
            ),
        )
        self.assertIsNotNone(_generic_event_in_frame(faded))
        self.assertIsNone(_generic_event_in_frame(gone))

    def test_visible_event_preview_uses_one_capture_and_ocr_pass(self) -> None:
        image = Image.new("RGB", (2560, 1440), "black")
        window = mock.Mock()
        window.capture.return_value = image
        preview_spans = (
            span("怀孕！", (764, 402), (717, 380, 812, 424)),
            span(
                "我等不及要将小婴儿抱在怀里了！",
                (932, 1043),
                (794, 1032, 1070, 1055),
            ),
        )
        with mock.patch(
            "xar_autoplayer.vision.ocr.ocr_spans",
            return_value=preview_spans,
        ) as ocr:
            detected, call_to_war, terminal = _visible_event_preview(window, 17)
        self.assertEqual(detected["title"], "怀孕！")
        self.assertEqual(detected["capture_sequence"], 17)
        self.assertIsNone(call_to_war)
        self.assertIsNone(terminal)
        window.capture.assert_called_once_with()
        ocr.assert_called_once_with(image, ACTIVE_EVENT_PREVIEW_REGION)

    def test_post_shortcut_event_distinguishes_fade_from_chained_event(self) -> None:
        def event_frame(sequence: int, title: str, option: str):
            return SimpleNamespace(
                observation_id=f"event-{sequence}",
                capture_sequence=sequence,
                client_rect=(0, 0, 2560, 1440),
                spans=(
                    span(title, (764, 402), (700, 380, 828, 424)),
                    span(option, (932, 1043), (780, 1032, 1084, 1055)),
                ),
            )

        source = _generic_event_in_frame(event_frame(1, "挑战", "接受挑战！"))
        driver = mock.Mock()
        driver.capture_once.side_effect = (
            event_frame(2, "优势", "点到为止！打得漂亮。"),
            event_frame(3, "优势", "点到为止！打得漂亮。"),
        )
        chained, last = _confirm_post_shortcut_event(
            driver, source, time.monotonic() + 1
        )
        self.assertEqual(chained["title"], "优势")
        self.assertEqual(last.observation_id, "event-3")

        gone = SimpleNamespace(
            observation_id="map-2",
            capture_sequence=2,
            client_rect=(0, 0, 2560, 1440),
            spans=(),
        )
        clear_driver = mock.Mock()
        clear_driver.capture_once.return_value = gone
        cleared, last = _confirm_post_shortcut_event(
            clear_driver, source, time.monotonic() + 1
        )
        self.assertIsNone(cleared)
        self.assertIs(last, gone)

    def test_generic_event_strategy_uses_visible_effects_and_first_tie_break(self) -> None:
        selected, score, reasons = _choose_generic_event_option(
            {
                "options": [
                    {"option_number": 1, "visible_text": "我会支付 50 金币。"},
                    {
                        "option_number": 2,
                        "visible_text": "我的威望将会增加 +25。",
                    },
                    {"option_number": 3, "visible_text": "以后再说吧。"},
                ]
            }
        )
        self.assertEqual(selected["option_number"], 2)
        self.assertGreater(score, 0)
        self.assertIn("增加:+65", reasons)
        self.assertLess(_score_generic_event_option("我将失去 -20 金币")[0], 0)

        tied, tied_score, tied_reasons = _choose_generic_event_option(
            {
                "options": [
                    {"option_number": 1, "visible_text": "就这么办。"},
                    {"option_number": 2, "visible_text": "当然可以。"},
                ]
            }
        )
        self.assertEqual(tied["option_number"], 1)
        self.assertEqual(tied_score, 0)
        self.assertEqual(tied_reasons, [])

    def test_keyboard_map_panel_summary_binds_two_visible_frames(self) -> None:
        def panel_frame(sequence: int, offset: int = 0):
            return SimpleNamespace(
                observation_id=f"realm-{sequence}",
                capture_sequence=sequence,
                client_rect=(0, 0, 2560, 1440),
                spans=(
                    span(
                        "我的领地",
                        (325 + offset, 78),
                        (270 + offset, 64, 380 + offset, 92),
                    ),
                    span("领地上限：6/7", (390, 210), (320, 196, 460, 224)),
                ),
            )

        summary = _panel_summary(
            "realm", "我的领地", panel_frame(4), panel_frame(5, 2)
        )
        self.assertEqual(summary["shortcut"], "f2")
        self.assertEqual(summary["frame_observation_ids"], ["realm-4", "realm-5"])
        self.assertIn("领地上限：6/7", summary["visible_text"])
        self.assertEqual(
            [item[2] for item in MAP_PANEL_SHORTCUTS],
            ["f2", "f3", "f4", "f8"],
        )
        with self.assertRaisesRegex(AgentError, "not consecutive"):
            _panel_summary("realm", "我的领地", panel_frame(4), panel_frame(6))

    def test_visible_building_offer_prefers_economic_text(self) -> None:
        frame = SimpleNamespace(
            client_rect=(0, 0, 2560, 1440),
            spans=(
                span("军营", (250, 320), (210, 307, 290, 333)),
                span("征召兵：+100", (340, 350), (270, 337, 410, 363)),
                span("修建", (620, 360), (590, 347, 650, 373)),
                span("农田与牧场", (250, 540), (180, 527, 320, 553)),
                span("税收：+0.5", (340, 570), (280, 557, 400, 583)),
                span("发展度增长：+5%", (350, 600), (270, 587, 430, 613)),
                span("修建", (620, 590), (590, 577, 650, 603)),
            ),
        )
        offers = _building_offer_summaries(frame)
        self.assertEqual(len(offers), 2)
        selected = _choose_economic_building_offer(frame)
        self.assertEqual(selected["offer_index"], 2)
        self.assertGreater(selected["strategy_score"], offers[0]["strategy_score"])
        self.assertEqual(
            len(
                _spans_with_text(
                    frame,
                    "农田与牧场",
                    region=(0.0, 0.30, 0.30, 0.50),
                )
            ),
            1,
        )

    def test_building_progress_matches_ck3_visible_completion_text(self) -> None:
        frame = SimpleNamespace(
            client_rect=(0, 0, 2560, 1440),
            spans=(
                span(
                    "22个月内完工简易牧场",
                    (1550, 410),
                    (1430, 397, 1670, 423),
                ),
            )
        )
        self.assertTrue(_building_construction_in_progress(frame))

    def test_steward_development_states_bind_visible_task_and_foggia(self) -> None:
        targeting = SimpleNamespace(
            client_rect=(0, 0, 2560, 1440),
            spans=(
                span("财政总管任务", (1280, 120), (1210, 104, 1350, 136)),
                span(
                    "提升伯爵领发展度",
                    (1280, 175),
                    (1160, 158, 1400, 192),
                ),
                span(
                    "点击地图上的一处地点指派任务",
                    (1280, 225),
                    (1080, 208, 1480, 242),
                ),
            ),
        )
        self.assertTrue(_steward_development_targeting_active(targeting))
        self.assertFalse(_steward_development_active(targeting))

        labeled_targeting = SimpleNamespace(
            client_rect=(0, 0, 2560, 1440),
            spans=targeting.spans
            + (span("福贾", (1131, 350), (1090, 332, 1172, 368)),),
        )
        self.assertEqual(
            _county_label_target_candidates(labeled_targeting, "福贾"),
            ((1131, 350), (1211, 350), (1131, 410), (1051, 350)),
        )

        confirmation = SimpleNamespace(
            client_rect=(0, 0, 2560, 1440),
            spans=(
                span(
                    "派遣你的财政总管前往福贾伯爵领执行提升伯爵领发展度任务。",
                    (1280, 620),
                    (850, 600, 1710, 640),
                ),
            ),
        )
        self.assertTrue(
            _steward_development_assignment_confirmation(confirmation)
        )

        active = SimpleNamespace(
            client_rect=(0, 0, 2560, 1440),
            spans=(
                span("内阁", (2124, 95), (2092, 78, 2156, 112)),
                span("财政总管", (2235, 546), (2194, 533, 2276, 560)),
                span("收税", (2160, 803), (2125, 786, 2195, 820)),
                span("在福贾伯爵领", (2230, 620), (2140, 604, 2320, 636)),
                span("剩余3年", (2230, 655), (2180, 639, 2280, 671)),
            ),
        )
        self.assertTrue(_steward_development_active(active))
        self.assertEqual(STEWARD_DEVELOP_COUNTY_TASK_CENTER, (2160, 803))
        self.assertIn((1220, 560), ROBERT_DEVELOPMENT_COUNTY_CANDIDATE_POINTS)

    def test_archived_steward_state_replays_without_ck3(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-opening-replay-") as temporary:
            artifact = Path(temporary) / "observation.json"
            artifact.write_text(
                json.dumps(
                    {
                        "format_version": 2,
                        "policy_observation": {
                            "observation_id": "f" * 32,
                            "screen": "unknown",
                            "ocr": [
                                {
                                    "text": "内阁",
                                    "center": [2124, 95],
                                    "bbox": [2092, 78, 2156, 112],
                                },
                                {
                                    "text": "财政总管",
                                    "center": [2235, 546],
                                    "bbox": [2194, 533, 2276, 560],
                                },
                                {
                                    "text": "收税",
                                    "center": [1798, 801],
                                    "bbox": [1772, 786, 1824, 817],
                                },
                                {
                                    "text": "在福贾伯爵领",
                                    "center": [2203, 855],
                                    "bbox": [2144, 844, 2262, 867],
                                },
                                {
                                    "text": "剩余3年",
                                    "center": [2304, 881],
                                    "bbox": [2269, 869, 2340, 894],
                                },
                            ],
                        },
                        "private_audit": {
                            "client_rect": [0, 0, 2560, 1440],
                            "capture_sequence": 10,
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            replay = replay_opening_observation(
                artifact, "steward-development-active"
            )
        self.assertTrue(replay["ok"])
        self.assertEqual(replay["mode"], "offline_observation_replay")
        self.assertEqual(replay["capture_sequence"], 10)

    def test_native_save_states_are_visibly_distinct(self) -> None:
        pause_menu = SimpleNamespace(
            client_rect=(0, 0, 2560, 1440),
            spans=(
                span("保存游戏", (1280, 520), (1200, 500, 1360, 540)),
                span("载入游戏", (1280, 590), (1200, 570, 1360, 610)),
                span("继续", (1280, 450), (1240, 430, 1320, 470)),
                span("退出游戏", (1280, 730), (1200, 710, 1360, 750)),
            ),
        )
        save_window = SimpleNamespace(
            client_rect=(0, 0, 2560, 1440),
            spans=(
                span("保存游戏", (1280, 360), (1200, 340, 1360, 380)),
                span("存档名：", (1120, 440), (1060, 420, 1180, 460)),
                span("保存", (1360, 1060), (1320, 1040, 1400, 1080)),
            ),
        )
        self.assertTrue(_pause_menu_visible(pause_menu))
        self.assertFalse(_save_window_visible(pause_menu))
        self.assertTrue(_save_window_visible(save_window))
        self.assertFalse(_pause_menu_visible(save_window))

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
    def test_auto_turn_routes_terminal_history_to_read_only_strategy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state"
            run = state / "runs" / "terminal-run"
            artifacts = run / "artifacts"
            artifacts.mkdir(parents=True)
            (run / "report.json").write_text(
                json.dumps(
                    {
                        "commands": [
                            {
                                "index": 1,
                                "command": "death-terminal",
                                "ok": True,
                                "result": {},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = _drive_opening(
                SimpleNamespace(state_dir=state),
                mock.Mock(),
                {},
                artifacts,
                run / "events.jsonl",
                Path("unused-contract.json"),
                "0" * 64,
                time.monotonic() + 5,
                development_step="auto-turn",
            )

        self.assertEqual(result["requested_step"], "auto-turn")
        self.assertEqual(result["step"], "strategy-review")
        self.assertEqual(result["auto_turn"]["phase"], "terminal")
        self.assertIsNone(result["window_binding"])

    def test_death_terminal_uses_heir_only_to_deliver_settlement(self) -> None:
        def frame(sequence: int, texts: tuple[str, ...], screen: str = "unknown"):
            spans = tuple(
                span(
                    text,
                    (
                        1280,
                        1120 if text == "继续扮演" else 300 + index * 80,
                    ),
                    (
                        900,
                        1095 if text == "继续扮演" else 275 + index * 80,
                        1660,
                        1145 if text == "继续扮演" else 325 + index * 80,
                    ),
                )
                for index, text in enumerate(texts)
            )
            return SimpleNamespace(
                capture_sequence=sequence,
                observation_id=f"handoff-{sequence}",
                screen=screen,
                spans=spans,
                controls=(),
                client_rect=(0, 0, 2560, 1440),
            )

        succession = ("你已过世", "继续扮演")
        settlement = (
            "轮回终结",
            "辛苦了，旅人。这一生的分量，我已仔细称过。",
            "最终分数：144",
            "很好。这笔账，已记入永恒。",
        )
        frames = [
            frame(1, succession),
            frame(2, succession),
            frame(3, succession),
            frame(4, ("游戏已暂停",), "map_hud"),
            frame(5, ("游戏已暂停",), "map_hud"),
            frame(6, settlement),
            frame(7, settlement),
            frame(8, ("正在观察",), "map_hud"),
            frame(9, ("正在观察",), "map_hud"),
            frame(10, ("继续", "保存游戏", "载入游戏", "退出游戏")),
            frame(11, ("继续", "保存游戏", "载入游戏", "退出游戏")),
            frame(12, ("退出游戏", "退出到主菜单", "退出到桌面", "取消")),
            frame(13, ("退出游戏", "退出到主菜单", "退出到桌面", "取消")),
            frame(14, ("退出游戏", "退出到主菜单", "退出到桌面", "取消")),
            frame(15, ("新游戏",), "main_menu"),
            frame(16, ("新游戏",), "main_menu"),
        ]
        window = mock.Mock(pid=10, hwnd=20, client_rect=(0, 0, 2560, 1440))
        window.request_foreground_without_input.return_value = {
            "status": "confirmed"
        }
        window.audit_binding.return_value = {"process": {"pid": 10}}
        driver = mock.Mock()
        driver.capture_once.side_effect = frames
        key_submit = mock.Mock(return_value=(2, 0))
        chord_submit = mock.Mock(return_value=(4, 0))
        click_submit = mock.Mock(return_value=(2, 0))
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state"
            artifacts = state / "runs" / "handoff-run" / "artifacts"
            artifacts.mkdir(parents=True)
            events = artifacts.parent / "events.jsonl"
            digest = hashlib.sha256(OPENING_CONTRACT.read_bytes()).hexdigest()
            with (
                mock.patch(
                    "xar_autoplayer.opening_smoke._bind_window",
                    return_value=window,
                ),
                mock.patch(
                    "xar_autoplayer.control.VisibleUiDriver",
                    return_value=driver,
                ),
                mock.patch(
                    "xar_autoplayer.control.executor._prepare_key_press_batch",
                    return_value=key_submit,
                ),
                mock.patch(
                    "xar_autoplayer.control.executor._prepare_key_chord_batch",
                    return_value=chord_submit,
                ),
                mock.patch(
                    "xar_autoplayer.control.executor._prepare_left_click_batch",
                    return_value=click_submit,
                ),
                mock.patch("pyautogui.moveTo"),
            ):
                result = _drive_opening(
                    SimpleNamespace(
                        expected_game_version="1.19.0.6",
                        state_dir=state,
                        profile_dir=state / "profile",
                        game_exe=Path("ck3.exe"),
                    ),
                    SimpleNamespace(
                        process=mock.Mock(poll=mock.Mock(return_value=None))
                    ),
                    {"display": {"language": "l_simp_chinese"}},
                    artifacts,
                    events,
                    OPENING_CONTRACT,
                    digest,
                    time.monotonic() + 60,
                    ordinary_event_count=0,
                    development_step="death-terminal",
                )
            history = read_one_life_strategy(state)

        self.assertEqual(result["final_screen"], "main_menu")
        self.assertTrue(result["terminal"]["technical_settlement_handoff"])
        self.assertEqual(result["terminal"]["heir_gameplay_actions"], 0)
        self.assertEqual(result["terminal"]["score"]["final"], 144)
        self.assertEqual(click_submit.call_count, 2)
        self.assertEqual(chord_submit.call_count, 1)
        self.assertEqual(key_submit.call_count, 4)
        self.assertEqual(history["episodes"][0]["successful_steps"], ["death-terminal"])
        self.assertFalse(history["continue_as_heir_after_death"])

    def test_death_terminal_confirms_settlement_and_returns_to_main_menu(
        self,
    ) -> None:
        def frame(sequence: int, texts: tuple[str, ...], screen: str = "unknown"):
            spans = tuple(
                span(
                    text,
                    (1280, 300 + index * 80),
                    (900, 275 + index * 80, 1660, 325 + index * 80),
                )
                for index, text in enumerate(texts)
            )
            return SimpleNamespace(
                capture_sequence=sequence,
                observation_id=f"death-{sequence}",
                screen=screen,
                spans=spans,
                controls=(),
                client_rect=(0, 0, 2560, 1440),
            )

        frames = [
            frame(
                1,
                (
                    "轮回终结",
                    "辛苦了，旅人。这一生的分量，我已仔细称过。",
                    "最终分数：88",
                    "很好。这笔账，已记入永恒。",
                ),
            ),
            frame(
                2,
                (
                    "轮回终结",
                    "辛苦了，旅人。这一生的分量，我已仔细称过。",
                    "最终分数：88",
                    "很好。这笔账，已记入永恒。",
                ),
            ),
            frame(3, ("正在观察",), "map_hud"),
            frame(4, ("正在观察",), "map_hud"),
            frame(5, ("继续", "保存游戏", "载入游戏", "退出游戏")),
            frame(6, ("继续", "保存游戏", "载入游戏", "退出游戏")),
            frame(7, ("退出游戏", "退出到主菜单", "退出到桌面", "取消")),
            frame(8, ("退出游戏", "退出到主菜单", "退出到桌面", "取消")),
            frame(9, ("退出游戏", "退出到主菜单", "退出到桌面", "取消")),
            frame(10, ("新游戏",), "main_menu"),
            frame(11, ("新游戏",), "main_menu"),
        ]
        window = mock.Mock(
            pid=10,
            hwnd=20,
            client_rect=(0, 0, 2560, 1440),
        )
        window.request_foreground_without_input.return_value = {
            "status": "confirmed"
        }
        window.audit_binding.return_value = {"process": {"pid": 10}}
        driver = mock.Mock()
        driver.capture_once.side_effect = frames
        key_submit = mock.Mock(return_value=(2, 0))
        chord_submit = mock.Mock(return_value=(4, 0))
        click_submit = mock.Mock(return_value=(2, 0))
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state"
            artifacts = state / "runs" / "death-run" / "artifacts"
            artifacts.mkdir(parents=True)
            events = artifacts.parent / "events.jsonl"
            digest = hashlib.sha256(OPENING_CONTRACT.read_bytes()).hexdigest()
            with (
                mock.patch(
                    "xar_autoplayer.opening_smoke._bind_window",
                    return_value=window,
                ),
                mock.patch(
                    "xar_autoplayer.control.VisibleUiDriver",
                    return_value=driver,
                ),
                mock.patch(
                    "xar_autoplayer.control.executor._prepare_key_press_batch",
                    return_value=key_submit,
                ),
                mock.patch(
                    "xar_autoplayer.control.executor._prepare_key_chord_batch",
                    return_value=chord_submit,
                ),
                mock.patch(
                    "xar_autoplayer.control.executor._prepare_left_click_batch",
                    return_value=click_submit,
                ),
                mock.patch("pyautogui.moveTo"),
            ):
                result = _drive_opening(
                    SimpleNamespace(
                        expected_game_version="1.19.0.6",
                        state_dir=state,
                        profile_dir=state / "profile",
                        game_exe=Path("ck3.exe"),
                    ),
                    SimpleNamespace(
                        process=mock.Mock(poll=mock.Mock(return_value=None))
                    ),
                    {"display": {"language": "l_simp_chinese"}},
                    artifacts,
                    events,
                    OPENING_CONTRACT,
                    digest,
                    time.monotonic() + 60,
                    ordinary_event_count=0,
                    development_step="death-terminal",
                )
        self.assertEqual(result["final_screen"], "main_menu")
        self.assertEqual(result["terminal"]["score"]["final"], 88)
        self.assertEqual(result["terminal"]["heir_gameplay_actions"], 0)
        self.assertTrue(result["terminal"]["returned_to_main_menu"])
        self.assertEqual(chord_submit.call_count, 1)
        self.assertEqual(key_submit.call_count, 2)
        self.assertEqual(click_submit.call_count, 1)

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
                    "lifestyle_authority_confirmation",
                ),
                (
                    "lifestyle_authority_confirmation.confirm",
                    "token-confirm-authority",
                    "lifestyle_martial_authority",
                ),
                (
                    "lifestyle_martial_authority.close",
                    "token-close-lifestyle",
                    "map_hud",
                ),
                ("map_hud.set_speed_five", "token-speed-five", "map_hud"),
                ("map_hud.resume", "token-resume", "map_running"),
                ("map_running.pause", "token-pause", "map_hud"),
            )
            source_screens = {
                "main_menu.new_game": "main_menu",
                "bookmark_lobby.select_robert": "bookmark_lobby",
                "bookmark_lobby.start_game": "bookmark_lobby_selected",
                "pact_event.accept_contract": "pact_event",
                "first_life_event.begin": "first_life_event",
                "blessing_event.option_1": "blessing_event",
                "curse_event.option_2": "curse_event",
                "map_hud.open_player_character": "map_hud",
                "map_hud.open_lifestyle": "map_hud",
                "lifestyle_selection.open_martial": "lifestyle_selection",
                "lifestyle_martial.select_authority_focus": (
                    "lifestyle_martial_unfocused"
                ),
                "lifestyle_authority_confirmation.confirm": (
                    "lifestyle_authority_confirmation"
                ),
                "lifestyle_martial_authority.close": (
                    "lifestyle_martial_authority"
                ),
                "map_hud.set_speed_five": "map_hud",
                "map_hud.resume": "map_hud",
                "map_running.pause": "map_running",
            }
            keyboard_controls = {
                "pact_event.accept_contract",
                "first_life_event.begin",
                "map_hud.open_player_character",
                "lifestyle_authority_confirmation.confirm",
                "lifestyle_martial_authority.close",
                "map_hud.set_speed_five",
                "map_hud.resume",
                "map_running.pause",
            }
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
                    screen=source_screens[control_id],
                    observation_id=f"before-{index}",
                    controls=(visible_control,),
                    frames=(),
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
                if control_id == "lifestyle_authority_confirmation.confirm":
                    driver.click_visible_control.return_value["observation"]["ocr"] = [
                        {"text": "军事生活方式"},
                        {"text": "生活方式重心"},
                        {"text": "当前：权威重心"},
                    ]
                if control_id in {
                    "lifestyle_martial_authority.close",
                    "map_hud.set_speed_five",
                }:
                    driver.click_visible_control.return_value["observation"]["ocr"] = [
                        {
                            "text": "公元1066年9月15日",
                            "bbox": [2079, 1407, 2285, 1433],
                        }
                    ]
                if control_id in {"map_hud.resume", "map_running.pause"}:
                    driver.click_visible_control.return_value["observation"]["ocr"] = [
                        {
                            "text": "公元1066年9月16日",
                            "bbox": [2079, 1407, 2285, 1433],
                        }
                    ]
                if control_id in keyboard_controls:
                    source = driver.observe_stable.return_value
                    post_policy = driver.click_visible_control.return_value[
                        "observation"
                    ]
                    after = SimpleNamespace(
                        screen=post_screen,
                        observation_id=f"obs-{index}",
                        controls=(),
                        latest=SimpleNamespace(spans=()),
                        to_policy_json=(
                            lambda payload=post_policy: dict(payload)
                        ),
                    )
                    driver.observe_stable.side_effect = (source, after)
                drivers.append(driver)
            escape_driver = mock.Mock()
            escape_driver.observe_stable.side_effect = (
                SimpleNamespace(
                    screen="player_character",
                    observation_id="obs-player-before-escape",
                    controls=(),
                    latest=SimpleNamespace(spans=()),
                ),
                SimpleNamespace(
                    screen="map_hud",
                    observation_id="obs-map-after-escape",
                    controls=(),
                    latest=SimpleNamespace(spans=()),
                    to_policy_json=lambda: {
                        "screen": "map_hud",
                        "observation_id": "obs-map-after-escape",
                    },
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
            blessing_source = SimpleNamespace(
                screen="blessing_event",
                observation_id="before-blessing",
                controls=tuple(blessing_choices),
                latest=SimpleNamespace(spans=tuple(blessing_spans)),
            )
            blessing_after_policy = blessing_driver.click_visible_control.return_value[
                "observation"
            ]
            blessing_driver.observe_stable.side_effect = (
                blessing_source,
                SimpleNamespace(
                    screen="curse_event",
                    observation_id=blessing_after_policy["observation_id"],
                    controls=(),
                    latest=SimpleNamespace(spans=()),
                    to_policy_json=(
                        lambda payload=blessing_after_policy: dict(payload)
                    ),
                ),
            )
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
            curse_source = SimpleNamespace(
                screen="curse_event",
                observation_id="before-curse",
                controls=tuple(curse_choices),
                latest=SimpleNamespace(spans=tuple(curse_spans)),
            )
            curse_after_policy = curse_driver.click_visible_control.return_value[
                "observation"
            ]
            curse_driver.observe_stable.side_effect = (
                curse_source,
                SimpleNamespace(
                    screen="map_hud",
                    observation_id=curse_after_policy["observation_id"],
                    controls=(),
                    latest=SimpleNamespace(spans=()),
                    to_policy_json=(lambda payload=curse_after_policy: dict(payload)),
                ),
            )
            first_event_driver = mock.Mock()

            def event_frame(sequence: int, y_offset: int = 0):
                return SimpleNamespace(
                    observation_id=f"ordinary-event-{sequence}",
                    capture_sequence=sequence,
                    client_rect=(0, 0, 2560, 1440),
                    spans=(
                        span(
                            "怀孕！",
                            (764, 402 + y_offset),
                            (717, 380, 812, 424),
                        ),
                        span(
                            "我等不及要将小婴儿抱在怀里了！",
                            (932, 1043 + y_offset),
                            (794, 1032, 1070, 1055),
                        ),
                    ),
                )

            first_event_driver.capture_once.side_effect = (
                event_frame(1),
                event_frame(2, 2),
            )
            first_post_driver = mock.Mock()
            first_post_driver.observe_stable.return_value = SimpleNamespace(
                screen="map_running",
                observation_id="map-after-first-ordinary-event",
                controls=(),
                latest=SimpleNamespace(
                    client_rect=(0, 0, 2560, 1440),
                    spans=(),
                ),
            )
            second_event_driver = mock.Mock()

            def second_event_frame(sequence: int, y_offset: int = 0):
                return SimpleNamespace(
                    observation_id=f"second-ordinary-event-{sequence}",
                    capture_sequence=sequence,
                    client_rect=(0, 0, 2560, 1440),
                    spans=(
                        span(
                            "领地的新机会",
                            (764, 402 + y_offset),
                            (690, 380, 838, 424),
                        ),
                        span(
                            "我会失去 -20 金币。",
                            (930, 988 + y_offset),
                            (820, 977, 1040, 1000),
                        ),
                        span(
                            "我的威望将会增加 +25。",
                            (930, 1043 + y_offset),
                            (790, 1032, 1070, 1055),
                        ),
                    ),
                )

            second_event_driver.capture_once.side_effect = (
                second_event_frame(1),
                second_event_frame(2, 2),
            )
            drivers.insert(16, first_event_driver)
            drivers.insert(17, first_post_driver)
            drivers.insert(18, second_event_driver)
            submit_key = mock.Mock(return_value=(2, 0))
            submit_chord = mock.Mock(return_value=(4, 0))
            with mock.patch(
                "xar_autoplayer.vision.BoundGameWindow.bind_session",
                return_value=window,
            ), mock.patch(
                "xar_autoplayer.control.VisibleUiDriver", side_effect=drivers
            ) as driver_type, mock.patch(
                "xar_autoplayer.control.executor._prepare_key_press_batch",
                return_value=submit_key,
            ) as prepare_key, mock.patch(
                "xar_autoplayer.control.executor._prepare_key_chord_batch",
                return_value=submit_chord,
            ) as prepare_chord, mock.patch(
                "xar_autoplayer.opening_smoke._visible_event_preview",
                side_effect=(
                    ({"candidate": 1}, None, None),
                    ({"candidate": 2}, None, None),
                ),
            ) as preview:
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
                    time.monotonic() + 300,
                    ordinary_event_count=2,
                )
            self.assertEqual(
                [item["control_id"] for item in result["actions"]],
                [item[0] for item in controls[:8]]
                + ["player_character.close"]
                + [item[0] for item in controls[8:-1]]
                + [
                    "ordinary_event.option_1",
                    "ordinary_event.option_2",
                    controls[-1][0],
                ],
            )
            self.assertEqual(driver_type.call_count, 20)
            self.assertEqual(preview.call_count, 2)
            initial_observation_timeout = drivers[0].observe_stable.call_args.args[1]
            self.assertGreater(initial_observation_timeout, 119.0)
            self.assertLessEqual(
                initial_observation_timeout, INITIAL_MAIN_MENU_TIMEOUT_SECONDS
            )
            for index in (0, 1, 2):
                drivers[index].click_visible_control.assert_called_once()
                self.assertEqual(
                    drivers[index].click_visible_control.call_args.args[0],
                    controls[index][1],
                )
            for driver_index, control_index in ((9, 8), (10, 9), (11, 10)):
                drivers[driver_index].click_visible_control.assert_called_once_with(
                    controls[control_index][1],
                    timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                )
            for index in (
                3,
                4,
                5,
                6,
                7,
                8,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
            ):
                drivers[index].click_visible_control.assert_not_called()
            self.assertEqual(
                [call.args[0] for call in prepare_key.call_args_list],
                [0x3B, 0x3B, 0x1C, 0x01, 0x06, 0x39, 0x39],
            )
            self.assertEqual(
                [call.args for call in prepare_chord.call_args_list],
                [
                    (0x2A, 0x02),
                    (0x2A, 0x02),
                    (0x2A, 0x02),
                    (0x2A, 0x03),
                    (0x2A, 0x02),
                    (0x2A, 0x03),
                ],
            )
            self.assertEqual(submit_key.call_count, 7)
            self.assertEqual(submit_chord.call_count, 6)
            event_rows = [
                json.loads(line)
                for line in events.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                [
                    row["key"]
                    for row in event_rows
                    if row["kind"] == "opening_key_input_planned"
                ],
                [
                    "shift+1",
                    "shift+1",
                    "shift+1",
                    "shift+2",
                    "f1",
                    "f1",
                    "enter",
                    "escape",
                    "5",
                    "space",
                    "shift+1",
                    "shift+2",
                    "space",
                ],
            )
            self.assertIn("长明的定力", result["first_blessing_choice"]["visible_text"])
            self.assertIn("军事经验", result["first_curse_choice"]["visible_text"])
            self.assertTrue(result["player_character_state"]["spouse_visible"])
            self.assertTrue(result["player_character_state"]["player_heir_visible"])
            self.assertEqual(result["lifestyle_state"]["focus"], "权威")
            self.assertEqual(
                result["first_ordinary_event"]["selected_option_number"], 1
            )
            self.assertEqual(result["first_ordinary_event"]["title"], "怀孕！")
            self.assertEqual(len(result["ordinary_events"]), 2)
            self.assertEqual(
                result["ordinary_events"][1]["selected_option_number"], 2
            )
            self.assertGreater(result["ordinary_events"][1]["strategy_score"], 0)
            self.assertEqual(result["time_progression"]["elapsed_days"], 1)
            self.assertEqual(result["final_screen"], "map_hud")

    def test_cli_exposes_opening_smoke(self) -> None:
        args = cli.parser().parse_args(["opening-smoke"])
        self.assertEqual(args.command, "opening-smoke")
        self.assertEqual(args.timeout, 900)
        self.assertEqual(args.ordinary_events, 3)
        custom = cli.parser().parse_args(
            ["opening-smoke", "--ordinary-events", "5", "--timeout", "1200"]
        )
        self.assertEqual(custom.ordinary_events, 5)
        self.assertEqual(custom.timeout, 1200)
        step = cli.parser().parse_args(["opening-step"])
        self.assertEqual(step.command, "opening-step")
        self.assertEqual(step.step, "steward-development")
        self.assertEqual(step.timeout, 240)
        auto_turn = cli.parser().parse_args(
            ["opening-step", "--step", "auto-turn"]
        )
        self.assertEqual(auto_turn.step, "auto-turn")
        self.assertIn("auto-turn", OPENING_DEVELOPMENT_STEPS)
        pause_map = cli.parser().parse_args(
            ["opening-step", "--step", "pause-map"]
        )
        self.assertEqual(pause_map.step, "pause-map")
        life_advance = cli.parser().parse_args(
            ["opening-step", "--step", "life-advance"]
        )
        self.assertEqual(life_advance.step, "life-advance")
        economic_step = cli.parser().parse_args(
            ["opening-step", "--step", "economic-event-cycle"]
        )
        self.assertEqual(economic_step.step, "economic-event-cycle")
        self.assertIn("economic-event-cycle", OPENING_DEVELOPMENT_STEPS)
        checkpoint_step = cli.parser().parse_args(
            ["opening-step", "--step", "save-checkpoint"]
        )
        self.assertEqual(checkpoint_step.step, "save-checkpoint")
        restore_step = cli.parser().parse_args(
            ["opening-step", "--step", "restore-checkpoint"]
        )
        self.assertEqual(restore_step.step, "restore-checkpoint")
        dynasty_step = cli.parser().parse_args(
            ["opening-step", "--step", "dynasty-review"]
        )
        self.assertEqual(dynasty_step.step, "dynasty-review")
        self.assertIn("dynasty-review", OPENING_DEVELOPMENT_STEPS)
        succession_step = cli.parser().parse_args(
            ["opening-step", "--step", "succession-review"]
        )
        self.assertEqual(succession_step.step, "succession-review")
        self.assertIn("succession-review", OPENING_DEVELOPMENT_STEPS)
        marriage_step = cli.parser().parse_args(
            ["opening-step", "--step", "marriage-review"]
        )
        self.assertEqual(marriage_step.step, "marriage-review")
        self.assertIn("marriage-review", OPENING_DEVELOPMENT_STEPS)
        marriage_action = cli.parser().parse_args(
            ["opening-step", "--step", "marriage-alliance"]
        )
        self.assertEqual(marriage_action.step, "marriage-alliance")
        self.assertIn("marriage-alliance", OPENING_DEVELOPMENT_STEPS)
        marriage_response = cli.parser().parse_args(
            ["opening-step", "--step", "marriage-confirm-response"]
        )
        self.assertEqual(marriage_response.step, "marriage-confirm-response")
        death_terminal = cli.parser().parse_args(
            ["opening-step", "--step", "death-terminal"]
        )
        self.assertEqual(death_terminal.step, "death-terminal")
        strategy_review = cli.parser().parse_args(["strategy-review"])
        self.assertEqual(strategy_review.command, "strategy-review")
        war_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-review"]
        )
        self.assertEqual(war_step.step, "war-review")
        self.assertIn("war-review", OPENING_DEVELOPMENT_STEPS)
        target_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-target-review"]
        )
        self.assertEqual(target_step.step, "war-target-review")
        interaction_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-interaction-review"]
        )
        self.assertEqual(interaction_step.step, "war-interaction-review")
        declaration_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-declaration-review"]
        )
        self.assertEqual(declaration_step.step, "war-declaration-review")
        casus_belli_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-casus-belli-review"]
        )
        self.assertEqual(casus_belli_step.step, "war-casus-belli-review")
        war_goal_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-goal-review"]
        )
        self.assertEqual(war_goal_step.step, "war-goal-review")
        war_declare_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-declare-palermo"]
        )
        self.assertEqual(war_declare_step.step, "war-declare-palermo")
        war_raise_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-raise-all"]
        )
        self.assertEqual(war_raise_step.step, "war-raise-all")
        war_move_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-move-palermo"]
        )
        self.assertEqual(war_move_step.step, "war-move-palermo")
        war_map_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-map-review"]
        )
        self.assertEqual(war_map_step.step, "war-map-review")
        war_find_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-find-palermo"]
        )
        self.assertEqual(war_find_step.step, "war-find-palermo")
        war_siege_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-siege-palermo"]
        )
        self.assertEqual(war_siege_step.step, "war-siege-palermo")
        war_advance_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-advance-week"]
        )
        self.assertEqual(war_advance_step.step, "war-advance-week")
        war_month_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-advance-month"]
        )
        self.assertEqual(war_month_step.step, "war-advance-month")
        war_status_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-status"]
        )
        self.assertEqual(war_status_step.step, "war-status")
        war_victory_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-enforce-demands"]
        )
        self.assertEqual(war_victory_step.step, "war-enforce-demands")
        war_disband_step = cli.parser().parse_args(
            ["opening-step", "--step", "war-disband-armies"]
        )
        self.assertEqual(war_disband_step.step, "war-disband-armies")
        resolve_event_step = cli.parser().parse_args(
            ["opening-step", "--step", "resolve-current-event"]
        )
        self.assertEqual(resolve_event_step.step, "resolve-current-event")
        dev_session = cli.parser().parse_args(["opening-dev-session"])
        self.assertEqual(dev_session.command, "opening-dev-session")
        self.assertEqual(dev_session.timeout, 21600)
        replay = cli.parser().parse_args(
            [
                "opening-replay",
                "--observation",
                "observation.json",
                "--check",
                "steward-development-active",
            ]
        )
        self.assertEqual(replay.command, "opening-replay")
        self.assertEqual(replay.observation, Path("observation.json"))


if __name__ == "__main__":
    unittest.main()
