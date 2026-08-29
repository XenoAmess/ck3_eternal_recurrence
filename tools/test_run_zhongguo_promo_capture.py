#!/usr/bin/env python3
"""Static contracts for the append-only ZhongGuo promo capture mode."""

from __future__ import annotations

from pathlib import Path
import inspect
import re
import sys


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
    assert body.index("assert_promo_frame_clean") < body.index("recorder.start()")
    for token in (
        '"reviewed_official_history_id": reviewed_history_id',
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
    ):
        assert token in close_body, token

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
    assert "acceptance.ensure_game_paused" in interruption_body
    assert "selected is None or kind is None" in interruption_body
    assert "len(dismissed) >= max_dismissals" in interruption_body

    sys.path.insert(0, str(ROOT / "tools"))
    import run_zhongguo_acceptance as capture

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
    validate_markers = inspect.getsource(capture.MarkerStream.validate)
    assert "if final:" in validate_markers
    assert "required_markers += REQUIRED_LATE_FIXTURE_MARKERS" in validate_markers
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
    assert jingcha_body.index(
        'acceptance.deliberate_click(host_option, "production host Jingcha option")'
    ) < jingcha_body.index("pause_after_jingcha_host_click")
    assert jingcha_body.index("pause_after_jingcha_host_click") < jingcha_body.index(
        "plan_button = acceptance.wait_for_ocr_text"
    )

    host_pause = inspect.getsource(capture.pause_after_jingcha_host_click)
    for token in (
        'acceptance.pyautogui.press("space")',
        "acceptance.read_hud_game_date",
        "date_freeze_probe",
        "len(set(observations[-3:])) == 1",
        "timeline pause after Jingcha host option",
        "stream.pump()",
        "PERSONAL_SWITCH_SCHEDULED_MARKER",
        "paused_day >= due_day",
        '"date_before_due": paused_day < due_day',
        '"last_three_dates_identical": frozen',
        '"09_jingcha_host_immediate_pause_gate.json"',
    ):
        assert token in host_pause, token
    assert "acceptance.ensure_game_paused" not in host_pause
    assert capture.JINGCHA_PERSONAL_SWITCH_DELAY_DAYS == 30

    interruption = inspect.getsource(capture.settle_promo_interruptions)
    assert "stop_event_title: str | None = None" in interruption
    assert "promo_event_title_evidence" in interruption
    assert interruption.index("promo_event_title_evidence") < interruption.index(
        "acceptance.select_stall_recovery"
    )
    assert "promo_preferred_product_event_option" in interruption
    assert "blocked_known_event_safe_option_missing" in interruption

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
    assert 'if grades[0] != "3.25"' in personal_body

    switch_advance = inspect.getsource(capture.advance_to_personal_switch)
    for token in (
        "timeout_s: float = 90.0",
        '"zg361_personal_switch", require_progress=True',
        "PERSONAL_SWITCH_SCHEDULED_MARKER",
        "settle_promo_interruptions",
        'stop_event_title="上司考定"',
        "zg361_personal_switch_resume_",
        "time.monotonic() + timeout_s",
    ):
        assert token in switch_advance, token

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
