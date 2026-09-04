#!/usr/bin/env python3
"""Static contracts for the append-only ZhongGuo promo capture mode."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import inspect
import json
import re
import sys
import tempfile
import threading
import types
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "tools" / "run_zhongguo_acceptance.py"
FIXTURE = ROOT / "tools" / "fixtures" / "zg361_acceptance"
SCOREBOARD_GUI = ROOT / "mod_zhongguo_style" / "gui" / "zg361_scoreboard.gui"
IDS = (1, 7, 20, 22, 26, 361)


def install_optional_desktop_import_stubs() -> None:
    """Keep static contract imports independent from live desktop packages."""
    attributes = {
        "pyautogui": (
            "FAILSAFE",
            "press",
            "hotkey",
            "moveTo",
            "click",
            "mouseDown",
            "mouseUp",
            "size",
        ),
        "numpy": (),
        "cv2": (),
        "win32api": ("GetKeyboardLayoutList",),
        "win32con": (),
        "win32gui": ("GetForegroundWindow", "GetWindowText"),
        "win32process": ("GetWindowThreadProcessId",),
    }
    for name, names in attributes.items():
        if importlib.util.find_spec(name) is None:
            module = types.ModuleType(name)
            for attribute in names:
                setattr(module, attribute, None)
            sys.modules[name] = module


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
    assert '"native_mcp_completed_before_received_board"' in received_body
    assert '"ocr_used_for_navigation_or_green": False' in received_body
    assert '"\u8ba4\u547d"' not in received_body
    assert '"\u4e0a\u53f8\u8003\u5b9a"' not in received_body
    assert "acceptance.ensure_game_paused" in received_body
    assert "settle_promo_interruptions" in received_body
    for token in (
        '"11_received_result_immediate_pause_gate.json"',
        'stream.count("ZGA: TEST PASS clean_policy_001_dispatched")',
        '"early_policy_001_marker_count"',
        'pause_evidence["result"] = "RED"',
        '"policy card 001 dispatched before received-scoreboard capture"',
    ):
        assert token in received_body, token
    assert "arm_native_speed_one" not in received_body
    assert "pause_after_promo_event_click" not in received_body
    assert "result_option" not in received_body
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

    install_optional_desktop_import_stubs()
    sys.path.insert(0, str(ROOT / "tools"))
    import run_zhongguo_acceptance as capture

    sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "tests" / "unit"))
    import test_zhongguo_ai_owned_case_snapshot_contract as ai_owned_snapshot_fixture
    import test_zhongguo_b2_pip_snapshot_v1_bridge as b2_snapshot_fixture
    import test_zhongguo_incident_snapshot_contract as incident_snapshot_fixture
    import test_zhongguo_workforce_collective_snapshot_v1_bridge as workforce_bridge_fixture
    import test_zhongguo_workforce_collective_snapshot_v1_contract as workforce_snapshot_fixture

    arm_source = inspect.getsource(capture.arm_native_speed_one)
    for token in (
        'service.execute_step("set-speed-1")',
        'submission.get("status") == "submitted"',
        'observed["date_raw"] != starting_date',
        'observed["active_event_instance_id"] != starting_event',
        "require_settled_revision",
        'snapshot.get("revision") != starting.get("revision")',
        'snapshot.get("paused") is True',
        '"settled_revision_observed": settled_revision_observed',
        'write_json(artifacts / f"{stem}_speed_one_gate.json", evidence)',
    ):
        assert token in arm_source, token
    identity_source = inspect.getsource(capture.query_event_definition_identity)
    for token in (
        "query_current_event_window_context_v1",
        "expected_revision=revision",
        'query.get("status") == "available"',
        'readiness.get("event_definition_identity_ready") is True',
        '"event_definition_key": event_definition_key',
    ):
        assert token in identity_source, token

    result_case_cell_source = inspect.getsource(
        capture.accept_zhongguo_result_case_snapshot_v1_live_cell
    )
    for token in (
        'tool_name = "ck3_query_zhongguo_result_case_snapshot_v1"',
        'notice_identity.get("event_definition_key") == "zg361.50"',
        'root_scope.get("raw_type_index") == 4',
        'root_scope.get("type_key") == "character"',
        'typed_identity.get("kind") == "character"',
        'subject_character_id == played_character_id',
        'row.get("name") == "zg361_notice_prompt_owner"',
        'row.get("name") == "zg361_reviewing_superior"',
        "visible_owner_character_id == owner_character_id",
        "service.query_zhongguo_result_case_snapshot_v1(",
        '"same_frame_positive_01"',
        '"same_frame_positive_02"',
        '"owner_filter_mismatch"',
        'typed_value(case, "state", "case") == 1',
        'typed_value(case, "grade", "case") == 1',
        '"kpi_frozen_q100000"',
        'typed_value(delivery, "method", "delivery") == 0',
        '"settlement_posted_serial"',
        '"player_subject_binding_ready": True',
        '"ready": True',
        "all_typed_leaves_unavailable(",
        '"connection_generation": connection_generation',
        "write_json(capability_path, capability_sidecar)",
        "write_json(requests_path, request_sidecar)",
        "write_json(responses_path, response_sidecar)",
    ):
        assert token in result_case_cell_source, token
    for forbidden in (
        "service.query_zhongguo_case_snapshot_v1(",
        "subject_character_id=",
        "case_kind=",
        "variable_name=",
        "unsupported_case_kind",
    ):
        assert forbidden not in result_case_cell_source, forbidden
    assert "wait_for_ocr" not in result_case_cell_source
    assert "deliberate_click" not in result_case_cell_source
    assert "HISTORICAL_TARGET" not in result_case_cell_source

    result_case_snapshot = {
        "revision": 73,
        "native_revision": 72,
        "snapshot_id": "native-headless:test:73",
        "date_raw": 53_182_008,
        "paused": True,
        "speed": 1,
        "active_event": {"instance_id": 51, "option_count": 2},
        "played_character": {"character_id": 441},
        "diagnostics": {"connection_generation": 4},
    }

    def saved_character_scope(
        name: str, name_identifier: int, character_id: int
    ) -> dict[str, object]:
        return {
            "name": name,
            "name_identifier": name_identifier,
            "scope": {
                "status": "available",
                "raw_type_index": 4,
                "type_key": "character",
                "subtype": 0,
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                },
            },
        }

    result_case_identity = {
        "event_instance_id": 51,
        "snapshot_revision": 73,
        "event_definition_key": "zg361.50",
        "query": {
            "status": "available",
            "current_event_window_context": {
                "event_definition_key": "zg361.50",
                "readiness": {
                    "event_definition_identity_ready": True,
                    "root_scope_ready": True,
                    "saved_scopes_ready": True,
                },
                "root_scope": {
                    "status": "available",
                    "raw_type_index": 4,
                    "type_key": "character",
                    "subtype": 0,
                    "typed_identity": {
                        "status": "available",
                        "kind": "character",
                        "character_id": 441,
                    },
                },
                # zg361.50 receives the prompt owner as an event saved scope;
                # its immediate block also publishes the visible alias.
                "saved_scopes": [
                    saved_character_scope(
                        "zg361_notice_prompt_owner", 97, 772
                    ),
                    saved_character_scope(
                        "zg361_reviewing_superior", 98, 772
                    ),
                ],
            },
        },
    }

    def result_available(value: object) -> dict[str, object]:
        return {
            "status": "available",
            "value": value,
            "unavailable_reason": None,
        }

    def result_unavailable() -> dict[str, object]:
        return {
            "status": "unavailable",
            "value": None,
            "unavailable_reason": "case_unavailable",
        }

    def positive_result_case_response(nonce: str) -> dict[str, object]:
        return {
            "schema_version": 3,
            "status": "available",
            "case_kind": "zhongguo.result.received-self",
            "request_nonce": nonce,
            "snapshot_revision": 72,
            "date_raw": 53_182_008,
            "paused": True,
            "player_character_id": 441,
            "subject_character_id": 441,
            "requested_owner_character_id": 772,
            "case": {
                "owner_character_id": result_available(772),
                "subject_character_id": result_available(441),
                "cycle_serial": result_available(7),
                "case_serial": result_available(903),
                "state": result_available(1),
                "grade": result_available(1),
            },
            "notice": {
                "absolute_grade": result_available(2),
                "kpi_frozen_q100000": result_available(7_654_321),
                "rank_frozen": result_available(4),
                "cohort_n_frozen": result_available(17),
            },
            "delivery": {
                "method": result_available(0),
                "objection_recorded": result_available(False),
                "settlement_posted_serial": result_available(0),
                "appeal_open": result_available(False),
            },
            "readiness": {
                "player_subject_binding_ready": True,
                "owner_binding_ready": True,
                "case_identity_ready": True,
                "notice_facts_ready": True,
                "delivery_state_ready": True,
                "same_frame_ready": True,
                "ready": True,
            },
            "unavailable_reason": None,
            "provenance": {"fixture": "exact-build"},
            "build": {"version": "1.19.0.6"},
            "source": {
                "snapshot_id": "native-headless:test:73",
                "revision": 73,
                "native_revision": 72,
            },
            "binding": {
                "request_nonce": nonce,
                "snapshot_id": "native-headless:test:73",
                "revision": 73,
                "native_revision": 72,
                "connection_generation": 4,
                "date_raw": 53_182_008,
                "paused": True,
                "player_character_id": 441,
                "subject_character_id": 441,
                "owner_character_id": 772,
                "expected_revision": 73,
            },
        }

    class ResultCaseSnapshotService:
        def __init__(self, *, leak_wrong_owner_leaf: bool = False) -> None:
            self.calls: list[dict[str, object]] = []
            self.leak_wrong_owner_leaf = leak_wrong_owner_leaf

        def snapshot(self) -> dict[str, object]:
            return copy.deepcopy(result_case_snapshot)

        def capabilities(self) -> dict[str, object]:
            return {
                "zhongguo_result_case_snapshot_v1_query_supported": True,
                "bridge_capabilities": [
                    "game.command.query-zhongguo-result-case-snapshot-v1"
                ],
            }

        def query_zhongguo_result_case_snapshot_v1(
            self,
            request_nonce: str,
            *,
            expected_revision: int,
            owner_character_id: int,
        ) -> dict[str, object]:
            self.calls.append(
                {
                    "request_nonce": request_nonce,
                    "expected_revision": expected_revision,
                    "owner_character_id": owner_character_id,
                }
            )
            assert expected_revision == 73
            if owner_character_id != 772:
                wrong_response: dict[str, object] = {
                    "schema_version": 1,
                    "case_kind": "zhongguo.result.received-self",
                    "request_nonce": request_nonce,
                    "status": "unavailable",
                    "unavailable_reason": "owner_filter_mismatch",
                    "snapshot_revision": 72,
                    "date_raw": 53_182_008,
                    "paused": True,
                    "player_character_id": 441,
                    "subject_character_id": 441,
                    "requested_owner_character_id": owner_character_id,
                    "case": {
                        field: result_unavailable()
                        for field in (
                            "owner_character_id",
                            "subject_character_id",
                            "cycle_serial",
                            "case_serial",
                            "state",
                            "grade",
                        )
                    },
                    "notice": {
                        field: result_unavailable()
                        for field in (
                            "absolute_grade",
                            "kpi_frozen_q100000",
                            "rank_frozen",
                            "cohort_n_frozen",
                        )
                    },
                    "delivery": {
                        field: result_unavailable()
                        for field in (
                            "method",
                            "objection_recorded",
                            "settlement_posted_serial",
                            "appeal_open",
                        )
                    },
                    "readiness": {
                        "player_subject_binding_ready": False,
                        "owner_binding_ready": False,
                        "case_identity_ready": False,
                        "notice_facts_ready": False,
                        "delivery_state_ready": False,
                        "same_frame_ready": True,
                        "ready": False,
                    },
                    "provenance": {"fixture": "exact-build"},
                    "build": {"version": "1.19.0.6"},
                    "source": {
                        "snapshot_id": "native-headless:test:73",
                        "revision": 73,
                        "native_revision": 72,
                    },
                    "binding": {
                        "request_nonce": request_nonce,
                        "snapshot_id": "native-headless:test:73",
                        "revision": 73,
                        "native_revision": 72,
                        "connection_generation": 4,
                        "date_raw": 53_182_008,
                        "paused": True,
                        "player_character_id": 441,
                        "subject_character_id": 441,
                        "owner_character_id": None,
                        "expected_revision": 73,
                    },
                }
                if self.leak_wrong_owner_leaf:
                    wrong_case = wrong_response["case"]
                    assert isinstance(wrong_case, dict)
                    wrong_case["case_serial"] = result_available(903)
                return wrong_response
            return positive_result_case_response(request_nonce)

    with tempfile.TemporaryDirectory() as temporary:
        artifacts = Path(temporary)
        result_case_service = ResultCaseSnapshotService()
        result_case = (
            capture.accept_zhongguo_result_case_snapshot_v1_live_cell(
                result_case_service,
                artifacts,
                notice_identity=result_case_identity,
                paused_snapshot=result_case_snapshot,
            )
        )
        assert result_case["result"] == "GREEN"
        assert result_case["case_kind"] == "zhongguo.result.received-self"
        assert result_case["binding"]["player_character_id"] == 441
        assert result_case["binding"]["subject_character_id"] == 441
        assert result_case["binding"]["owner_character_id"] == 772
        assert result_case["owner_scope_observation"] == {
            "zg361_notice_prompt_owner_count": 1,
            "zg361_reviewing_superior_count": 1,
            "selected_owner_scope": "zg361_notice_prompt_owner",
            "visible_cross_check": "matched",
        }
        assert [
            call["owner_character_id"] for call in result_case_service.calls
        ] == [772, 772, 773]
        for call in result_case_service.calls:
            assert set(call) == {
                "request_nonce",
                "expected_revision",
                "owner_character_id",
            }
        for suffix in (
            "capabilities.json",
            "requests.json",
            "responses.json",
            "gate.json",
        ):
            assert (
                artifacts
                / f"10_phase2_325_notice_result_case_snapshot_v1_{suffix}"
            ).is_file()
        stored_requests = json.loads(
            (
                artifacts
                / "10_phase2_325_notice_result_case_snapshot_v1_requests.json"
            ).read_text(encoding="utf-8")
        )
        stored_responses = json.loads(
            (
                artifacts
                / "10_phase2_325_notice_result_case_snapshot_v1_responses.json"
            ).read_text(encoding="utf-8")
        )
        assert len(stored_requests["requests"]) == 3
        for stored_request in stored_requests["requests"]:
            arguments = stored_request["arguments"]
            assert set(arguments) == {
                "request_nonce",
                "expected_revision",
                "owner_character_id",
            }
            assert "subject_character_id" not in arguments
            assert "case_kind" not in arguments
            assert "variable_name" not in arguments
        first_positive = stored_responses["responses"][0]["response"]
        assert first_positive["case"]["state"]["value"] == 1
        assert first_positive["case"]["grade"]["value"] == 1
        assert (
            first_positive["notice"]["kpi_frozen_q100000"]["value"]
            == 7_654_321
        )
        assert first_positive["delivery"]["method"]["value"] == 0
        assert (
            first_positive["delivery"]["objection_recorded"]["value"]
            is False
        )
        assert (
            first_positive["delivery"]["settlement_posted_serial"]["value"]
            == 0
        )
        assert first_positive["delivery"]["appeal_open"]["value"] is False
        wrong_response = stored_responses["responses"][2]["response"]
        assert wrong_response["unavailable_reason"] == "owner_filter_mismatch"
        expected_wrong_leaf_counts = {
            "case": 6,
            "notice": 4,
            "delivery": 4,
        }
        for group_name, expected_count in expected_wrong_leaf_counts.items():
            group = wrong_response[group_name]
            typed_leaves = list(group.values())
            assert len(typed_leaves) == expected_count
            assert all(
                leaf == result_unavailable() for leaf in typed_leaves
            ), group_name
        stored_gate = json.loads(
            (
                artifacts
                / "10_phase2_325_notice_result_case_snapshot_v1_gate.json"
            ).read_text(encoding="utf-8")
        )
        assert stored_gate["checks"][
            "wrong_owner_all_typed_leaves_unavailable"
        ] == expected_wrong_leaf_counts
        assert stored_gate["observed_result_case"]["case"] == {
            "owner_character_id": 772,
            "subject_character_id": 441,
            "cycle_serial": 7,
            "case_serial": 903,
            "state": 1,
            "grade": 1,
        }

    with tempfile.TemporaryDirectory() as temporary:
        leaking_service = ResultCaseSnapshotService(
            leak_wrong_owner_leaf=True
        )
        try:
            capture.accept_zhongguo_result_case_snapshot_v1_live_cell(
                leaking_service,
                Path(temporary),
                notice_identity=result_case_identity,
                paused_snapshot=result_case_snapshot,
            )
        except capture.acceptance.RunnerError as error:
            assert "wrong-owner query" in str(error)
        else:
            raise AssertionError(
                "result-case cell accepted a wrong-owner semantic leak"
            )

    bad_identity = copy.deepcopy(result_case_identity)
    bad_identity["query"]["current_event_window_context"]["root_scope"] = None
    with tempfile.TemporaryDirectory() as temporary:
        bad_service = ResultCaseSnapshotService()
        try:
            capture.accept_zhongguo_result_case_snapshot_v1_live_cell(
                bad_service,
                Path(temporary),
                notice_identity=bad_identity,
                paused_snapshot=result_case_snapshot,
            )
        except capture.acceptance.RunnerError as error:
            assert "root scope is not a typed character" in str(error)
        else:
            raise AssertionError(
                "result-case cell accepted a missing typed root scope"
            )
        assert bad_service.calls == []
        bad_gate = json.loads(
            (
                Path(temporary)
                / "10_phase2_325_notice_result_case_snapshot_v1_gate.json"
            ).read_text(encoding="utf-8")
        )
        assert bad_gate["result"] == "RED"
        assert bad_gate["fixture_character_id_used"] is False

    impossible_owner_snapshot = copy.deepcopy(result_case_snapshot)
    impossible_owner_snapshot["played_character"]["character_id"] = 772
    with tempfile.TemporaryDirectory() as temporary:
        impossible_service = ResultCaseSnapshotService()
        try:
            capture.accept_zhongguo_result_case_snapshot_v1_live_cell(
                impossible_service,
                Path(temporary),
                notice_identity=result_case_identity,
                paused_snapshot=impossible_owner_snapshot,
            )
        except capture.acceptance.RunnerError as error:
            assert "root is not the played reviewed subject" in str(error)
        else:
            raise AssertionError(
                "result-case cell accepted the owner as received-self subject"
            )
        assert impossible_service.calls == []

    mismatched_visible_identity = copy.deepcopy(result_case_identity)
    mismatched_visible_scopes = mismatched_visible_identity["query"][
        "current_event_window_context"
    ]["saved_scopes"]
    mismatched_visible_scopes[1]["scope"]["typed_identity"][
        "character_id"
    ] = 773
    with tempfile.TemporaryDirectory() as temporary:
        mismatched_service = ResultCaseSnapshotService()
        try:
            capture.accept_zhongguo_result_case_snapshot_v1_live_cell(
                mismatched_service,
                Path(temporary),
                notice_identity=mismatched_visible_identity,
                paused_snapshot=result_case_snapshot,
            )
        except capture.acceptance.RunnerError as error:
            assert "does not match the notice prompt owner" in str(error)
        else:
            raise AssertionError(
                "result-case cell accepted mismatched visible owner scopes"
            )
        assert mismatched_service.calls == []

    primary_only_identity = copy.deepcopy(result_case_identity)
    primary_only_identity["query"]["current_event_window_context"][
        "saved_scopes"
    ] = primary_only_identity["query"]["current_event_window_context"][
        "saved_scopes"
    ][:1]
    with tempfile.TemporaryDirectory() as temporary:
        primary_only_result = (
            capture.accept_zhongguo_result_case_snapshot_v1_live_cell(
                ResultCaseSnapshotService(),
                Path(temporary),
                notice_identity=primary_only_identity,
                paused_snapshot=result_case_snapshot,
            )
        )
        assert primary_only_result["owner_scope_observation"][
            "visible_cross_check"
        ] == "not_published"

    policy_option_source = inspect.getsource(
        capture.select_resolved_event_option_native
    )
    for token in (
        "query_event_definition_identity",
        'readiness.get("option_presentation_ready") is True',
        'option.get("shown") is True',
        'option.get("enabled") is True',
        'option.get("resolved_name")',
        'matches[0].get("native_option_index")',
        "service.select_event_option(",
        "event_instance_id=event_instance_id",
        "expected_revision=revision",
        '"selection_method": "native_mcp_resolved_option"',
    ):
        assert token in policy_option_source, token
    assert "wait_for_ocr_text" not in policy_option_source
    assert "deliberate_click" not in policy_option_source

    class PolicyOptionService:
        def __init__(self, *, enabled: bool = True) -> None:
            self.enabled = enabled
            self.query_calls: list[tuple[int, int]] = []
            self.selections: list[tuple[int, int | None, int | None]] = []

        def query_current_event_window_context_v1(
            self, event_instance_id: int, *, expected_revision: int
        ) -> dict[str, object]:
            self.query_calls.append((event_instance_id, expected_revision))
            return {
                "status": "available",
                "current_event_window_context": {
                    "event_definition_key": "zg361m.7",
                    "readiness": {
                        "event_definition_identity_ready": True,
                        "option_presentation_ready": True,
                    },
                    "options": [
                        {
                            "native_option_index": 0,
                            "shown": True,
                            "enabled": self.enabled,
                            "resolved_name": (
                                "只邀请有真实协作的少数评价者，要求具体案例并交叉核验，"
                                "承担邀评与去重工时。"
                            ),
                        },
                        {
                            "native_option_index": 1,
                            "shown": True,
                            "enabled": True,
                            "resolved_name": "广撒邀评并立刻按高低票加权。",
                        },
                        {
                            "native_option_index": 2,
                            "shown": True,
                            "enabled": True,
                            "resolved_name": "这季度先不碰，登记制度债",
                        },
                    ],
                },
            }

        def select_event_option(
            self,
            option_number: int,
            *,
            event_instance_id: int | None = None,
            expected_revision: int | None = None,
        ) -> dict[str, object]:
            self.selections.append(
                (option_number, event_instance_id, expected_revision)
            )
            return {
                "step": f"select-event-option-{option_number}",
                "accepted": True,
                "status": "submitted",
            }

    policy_option_snapshot = {
        "revision": 56,
        "native_revision": 55,
        "date_raw": 53146896,
        "paused": True,
        "speed": 1,
        "active_event": {"instance_id": 7, "option_count": 3},
        "played_character": {"character_id": 77},
    }
    with tempfile.TemporaryDirectory() as temp_dir:
        policy_option_service = PolicyOptionService()
        policy_option_gate = capture.select_resolved_event_option_native(
            policy_option_service,
            Path(temp_dir),
            policy_option_snapshot,
            stem="12_policy_007_close",
            expected_event_definition_key="zg361m.7",
            expected_option_text="只邀请有真实协作",
        )
        assert policy_option_service.query_calls == [(7, 56)]
        assert policy_option_service.selections == [(1, 7, 56)]
        assert policy_option_gate["result"] == "GREEN"
        assert policy_option_gate["selected_native_option_index"] == 0
        assert policy_option_gate["selected_option_number"] == 1
        persisted_policy_option_gate = json.loads(
            (
                Path(temp_dir)
                / "12_policy_007_close_native_option_selection_gate.json"
            ).read_text(encoding="utf-8")
        )
        assert persisted_policy_option_gate["result"] == "GREEN"
        assert persisted_policy_option_gate["selection_submission"][
            "status"
        ] == "submitted"

    with tempfile.TemporaryDirectory() as temp_dir:
        disabled_policy_option_service = PolicyOptionService(enabled=False)
        try:
            capture.select_resolved_event_option_native(
                disabled_policy_option_service,
                Path(temp_dir),
                policy_option_snapshot,
                stem="12_policy_007_disabled",
                expected_event_definition_key="zg361m.7",
                expected_option_text="只邀请有真实协作",
            )
        except capture.acceptance.RunnerError as error:
            assert "exactly one configured option" in str(error)
        else:
            raise AssertionError("disabled policy option did not fail closed")
        assert disabled_policy_option_service.selections == []
        disabled_policy_option_gate = json.loads(
            (
                Path(temp_dir)
                / "12_policy_007_disabled_native_option_selection_gate.json"
            ).read_text(encoding="utf-8")
        )
        assert disabled_policy_option_gate["result"] == "RED"
        assert disabled_policy_option_gate["matched_options"] == []
    pause_source = inspect.getsource(capture.pause_after_promo_event_click)
    for token in (
        "transition_deadline = time.monotonic() + 0.75",
        'observed["date_raw"] != pre_date',
        'observed["active_event_instance_id"] != pre_event',
        'transition_snapshot.get("paused") is False',
        'service.execute_step("pause-map")',
        'pause_submission.get("status") == "submitted"',
        'all(item["date_raw"] == pre_date for item in tail)',
        "query_event_definition_identity",
        "instance_transitioned or definition_transitioned",
    ):
        assert token in pause_source, token
    assert pause_source.index('transition_snapshot.get("paused") is False') < (
        pause_source.index('service.execute_step("pause-map")')
    )

    class SpeedOneService:
        def __init__(self) -> None:
            self.steps: list[str] = []
            self.snapshots = [
                {
                    "revision": 1,
                    "native_revision": 1,
                    "date_raw": 200,
                    "paused": False,
                    "speed": 5,
                    "active_event": {"instance_id": 9},
                    "played_character": {"character_id": 77},
                },
                {
                    "revision": 2,
                    "native_revision": 2,
                    "date_raw": 200,
                    "paused": False,
                    "speed": 5,
                    "active_event": {"instance_id": 9},
                    "played_character": {"character_id": 77},
                },
            ]

        def execute_step(self, step: str) -> dict[str, object]:
            self.steps.append(step)
            return {"step": step, "accepted": True, "status": "submitted"}

        def snapshot(self) -> dict[str, object]:
            return self.snapshots.pop(0)

    speed_one_service = SpeedOneService()
    with tempfile.TemporaryDirectory() as temp_dir:
        speed_one_gate = capture.arm_native_speed_one(
            speed_one_service,
            Path(temp_dir),
            stem="mock_received_result",
        )
        assert speed_one_service.steps == ["set-speed-1"]
        assert speed_one_gate["result"] == "GREEN"
        assert speed_one_gate["snapshot"]["paused"] is False
        assert speed_one_gate["speed_one_observed_pre_click"] is False
        assert (
            Path(temp_dir) / "mock_received_result_speed_one_gate.json"
        ).is_file()

    class DelayedSpeedOneService:
        def __init__(self) -> None:
            self.steps: list[str] = []
            self.snapshots = [
                {
                    "revision": revision,
                    "native_revision": revision,
                    "date_raw": 200,
                    "paused": True,
                    "speed": speed,
                    "active_event": {"instance_id": 9, "option_count": 3},
                    "played_character": {"character_id": 77},
                }
                for revision, speed in ((10, 5), (10, 5), (10, 5), (11, 1))
            ]

        def execute_step(self, step: str) -> dict[str, object]:
            self.steps.append(step)
            return {"step": step, "accepted": True, "status": "submitted"}

        def snapshot(self) -> dict[str, object]:
            return self.snapshots.pop(0)

    delayed_speed_one_service = DelayedSpeedOneService()
    with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
        capture.time, "sleep"
    ):
        delayed_speed_one_gate = capture.arm_native_speed_one(
            delayed_speed_one_service,
            Path(temp_dir),
            stem="mock_typed_policy_option",
            require_settled_revision=True,
        )
        assert delayed_speed_one_service.steps == ["set-speed-1"]
        assert delayed_speed_one_gate["result"] == "GREEN"
        assert delayed_speed_one_gate["settled_revision_required"] is True
        assert delayed_speed_one_gate["settled_revision_observed"] is True
        assert delayed_speed_one_gate["snapshot"]["revision"] == 11
        assert len(delayed_speed_one_gate["observations"]) == 3

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
            expected_predecessor_event_key="zg361.4",
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

    class AlreadyPausedAfterCloseService:
        def __init__(self) -> None:
            self.steps: list[str] = []
            self.snapshots = [
                {
                    "revision": 2,
                    "native_revision": 2,
                    "date_raw": 200,
                    "paused": True,
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
            return self.snapshots.pop(0)

        def execute_step(self, step: str) -> dict[str, object]:
            self.steps.append(step)
            raise AssertionError("pause-map must not toggle an already-paused map")

    with tempfile.TemporaryDirectory() as temp_dir:
        already_paused_service = AlreadyPausedAfterCloseService()
        already_paused = capture.pause_after_promo_event_click(
            already_paused_service,
            Path(temp_dir),
            pre_click,
            stem="mock_already_paused",
            expected_predecessor_event_key="zg361.4",
        )
        assert already_paused["result"] == "GREEN"
        assert already_paused["transition_failure"] is None
        assert already_paused["already_paused_after_event_transition"] is True
        assert already_paused_service.steps == []

    class SameInstanceDefinitionTransitionService:
        def __init__(self, definition_key: str) -> None:
            self.definition_key = definition_key
            self.steps: list[str] = []
            self.query_calls: list[tuple[int, int]] = []

        def snapshot(self) -> dict[str, object]:
            return {
                "revision": 12,
                "native_revision": 11,
                "date_raw": 200,
                "paused": True,
                "speed": 1,
                "active_event": {"instance_id": 9, "option_count": 4},
                "played_character": {"character_id": 77},
            }

        def execute_step(self, step: str) -> dict[str, object]:
            self.steps.append(step)
            raise AssertionError("pause-map must not toggle an already-paused map")

        def query_current_event_window_context_v1(
            self, event_instance_id: int, *, expected_revision: int
        ) -> dict[str, object]:
            self.query_calls.append((event_instance_id, expected_revision))
            return {
                "status": "available",
                "current_event_window_context": {
                    "event_definition_key": self.definition_key,
                    "readiness": {"event_definition_identity_ready": True},
                },
            }

    def advancing_clock() -> object:
        value = 0.0

        def tick() -> float:
            nonlocal value
            value += 0.2
            return value

        return tick

    with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
        capture.time, "monotonic", side_effect=advancing_clock()
    ), mock.patch.object(capture.time, "sleep", return_value=None):
        chained_service = SameInstanceDefinitionTransitionService("zg361.6")
        chained = capture.pause_after_promo_event_click(
            chained_service,
            Path(temp_dir),
            pre_click,
            stem="mock_same_instance_new_definition",
            expected_predecessor_event_key="zg361m.1",
        )
        assert chained["result"] == "GREEN"
        assert chained["instance_transition_seen_same_date"] is False
        assert chained["definition_transition_seen_same_date"] is True
        assert chained["event_transition_identity_method"] == "event_definition_key"
        assert chained["observed_successor_event_key"] == "zg361.6"
        assert chained["transition_failure"] is None
        assert chained_service.query_calls == [(9, 12)]
        assert chained_service.steps == []

    with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
        capture.time, "monotonic", side_effect=advancing_clock()
    ), mock.patch.object(capture.time, "sleep", return_value=None):
        policy_successor_service = SameInstanceDefinitionTransitionService(
            "zg361m.22"
        )
        policy_successor = capture.pause_after_promo_event_click(
            policy_successor_service,
            Path(temp_dir),
            pre_click,
            stem="mock_policy_020_same_instance_policy_022",
            expected_predecessor_event_key="zg361m.20",
        )
        assert policy_successor["result"] == "GREEN"
        assert policy_successor["instance_transition_seen_same_date"] is False
        assert policy_successor["definition_transition_seen_same_date"] is True
        assert policy_successor["event_transition_identity_method"] == (
            "event_definition_key"
        )
        assert policy_successor["observed_successor_event_key"] == "zg361m.22"
        assert policy_successor_service.query_calls == [(9, 12)]

    with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
        capture.time, "monotonic", side_effect=advancing_clock()
    ), mock.patch.object(capture.time, "sleep", return_value=None), mock.patch.object(
        capture.acceptance.ImageGrab,
        "grab",
        return_value=SimpleNamespace(save=lambda _path: None),
    ):
        unchanged_service = SameInstanceDefinitionTransitionService("zg361m.1")
        try:
            capture.pause_after_promo_event_click(
                unchanged_service,
                Path(temp_dir),
                pre_click,
                stem="mock_same_instance_same_definition",
                expected_predecessor_event_key="zg361m.1",
            )
        except capture.acceptance.RunnerError:
            pass
        else:
            raise AssertionError("same event instance and definition must fail")
        unchanged_gate = json.loads(
            (
                Path(temp_dir)
                / "mock_same_instance_same_definition_immediate_pause_gate.json"
            ).read_text(encoding="utf-8")
        )
        assert unchanged_gate["result"] == "RED"
        assert unchanged_gate["definition_transition_seen_same_date"] is False
        assert unchanged_gate["observed_successor_event_key"] == "zg361m.1"
        assert unchanged_service.query_calls == [(9, 12)]

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
                expected_predecessor_event_key="zg361.4",
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

    # Phase-two case events may bind their already-frozen case owner, while
    # the legacy delayed result trio must still reject a live review read.
    events_path = capture.SOURCE / "events" / "zg361_events.txt"
    authoritative_events = events_path.read_text(encoding="utf-8-sig")
    phase2_marker = "# 玩家封臣：3.25 正式送达、见证送达、申诉时钟与个人清算单"
    assert phase2_marker in authoritative_events
    legacy_live_read = authoritative_events.replace(
        phase2_marker,
        "save_scope_as = zg361_reviewing_superior\n" + phase2_marker,
        1,
    )

    def read_text_with_legacy_live_read(
        path: Path, *args: object, **kwargs: object
    ) -> str:
        if path.resolve() == events_path.resolve():
            return legacy_live_read
        return original_read_text(path, *args, **kwargs)

    with mock.patch.object(Path, "read_text", read_text_with_legacy_live_read):
        legacy_live_read_errors = capture.product_source_errors()
    assert (
        "delayed result events must not re-read live review data"
        in legacy_live_read_errors
    ), legacy_live_read_errors

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
        canonical_seed_contract = capture.load_phase2_seed_contract()
        assert canonical_seed_contract["status"] == "ready"
        assert canonical_seed_contract["ready"] is True
        assert canonical_seed_contract["blocker"] == ""
        assert canonical_seed_contract["provenance"]["limitations"]
        assert canonical_seed_contract["saved_state"]["played_character_id"] == 29037
        assert canonical_seed_contract["saved_state"]["player_history_id"] == (
            capture.PHASE2_SEED_PLAYER_HISTORY_ID
        )
        assert canonical_seed_contract["source"]["sha256"] != (
            "98687d21fe816a4a42d1d6bef85cea9d8a0ed9e74d53cdeadf653b0d3a57ecb3"
        )
        assert canonical_seed_contract["domain_query_matrix"] == {
            "schema_version": 1,
            "b2_pip_owner_character_id": 32904,
            "incident_owner_character_id": 32904,
            "workforce_owner_character_id": 32904,
            "ai_owned_case_owner_character_id": 32904,
            "ai_owned_case_subject_character_id": 29037,
        }

        blocked_seed_contract = copy.deepcopy(canonical_seed_contract)
        blocked_seed_contract["status"] = "blocked_runtime_tree_mismatch"
        blocked_seed_contract["ready"] = False
        blocked_seed_contract["blocker"] = "deliberate blocked seed fixture"
        blocked_seed_path = temporary_root / "blocked-seed-contract.json"
        blocked_seed_path.write_text(
            json.dumps(blocked_seed_contract), encoding="utf-8"
        )
        try:
            capture.preflight_phase2_seed_contract(blocked_seed_path)
        except capture.acceptance.RunnerError as error:
            assert "phase-two seed preflight RED" in str(error)
            assert "deliberate blocked seed fixture" in str(error)
        else:
            raise AssertionError("blocked phase-two seed passed preflight")

        seed_source_profile = temporary_root / "seed-source-profile"
        seed_source_save = seed_source_profile / "save games" / "seed.ck3"
        seed_source_save.parent.mkdir(parents=True)
        seed_source_save.write_bytes(
            b"SAV0101" + b"\0" * 24 + b"1.19.0.6" + b"\0" * 128
        )
        seed_source_stat = seed_source_save.stat()
        seed_product_tree = "b" * 64
        seed_fixture_tree = "c" * 64
        seed_domain_query_matrix = {
            "schema_version": 1,
            "b2_pip_owner_character_id": 9100,
            "incident_owner_character_id": 9200,
            "workforce_owner_character_id": 9300,
            "ai_owned_case_owner_character_id": 9400,
            "ai_owned_case_subject_character_id": 9001,
        }
        seed_enabled_mods = [
            f"mod/{capture.PRODUCT_OUTER}",
            f"mod/{capture.FIXTURE_OUTER}",
        ]
        seed_source_run = temporary_root / "seed-source-run"
        seed_source_run.mkdir()
        seed_source_report = {
            "result": "GREEN",
            "cell": {
                "result": "GREEN",
                "game_version": capture.EXPECTED_GAME_VERSION,
                "ck3_executable_before_sha256": capture.EXPECTED_EXE_SHA256,
                "ck3_executable_after_sha256": capture.EXPECTED_EXE_SHA256,
                "enabled_mods": seed_enabled_mods,
                "runtime_tree_before_sha256": {
                    "product": seed_product_tree,
                    "fixture": seed_fixture_tree,
                },
                "runtime_tree_after_sha256": {
                    "product": seed_product_tree,
                    "fixture": seed_fixture_tree,
                },
                "runtime_trees_unchanged": True,
                "isolated_userdir_path": str(seed_source_profile.resolve()),
                "scenario_evidence": {
                    "player_history_id": (
                        capture.PHASE2_SEED_PLAYER_HISTORY_ID
                    ),
                    "historical_subjects_manufactured_by_fixture": False,
                    "ocr_used": False,
                    "test_decision_used": False,
                    "phase2_seed_bootstrap_attestation": {
                        "event_definition_key": "zga_phase2_seed.1",
                        "player_history_id": (
                            capture.PHASE2_SEED_PLAYER_HISTORY_ID
                        ),
                        "played_character_id": 9001,
                        "domain_query_matrix": seed_domain_query_matrix,
                        "mcp_only": True,
                        "event_close": {
                            "step": "select-event-option-1",
                            "postcondition_verified": True,
                        },
                        "checkpoint": {
                            "status": "saved",
                            "path": str(seed_source_save.resolve()),
                            "size": seed_source_stat.st_size,
                            "sha256": capture.isolated.sha256_file(
                                seed_source_save
                            ),
                            "date_raw": 777,
                            "episode_character_id": 9001,
                        },
                    },
                    "phase2_seed_snapshot": {
                        "paused": True,
                        "map_ready": True,
                        "date_raw": 777,
                        "played_character": {
                            "character_id": 9001,
                            "alive": True,
                        }
                    },
                },
            },
        }
        seed_source_report_path = seed_source_run / "report.json"
        seed_source_report_path.write_text(
            json.dumps(seed_source_report), encoding="utf-8"
        )
        seed_source_index_path = seed_source_run / "evidence-index.json"
        seed_source_index_path.write_text(
            json.dumps({"result": "GREEN", "files": []}), encoding="utf-8"
        )
        ready_seed_contract = {
            "schema_version": 1,
            "kind": "zg361_phase2_paused_seed",
            "status": "ready",
            "ready": True,
            "blocker": "",
            "source": {
                "profile": str(seed_source_profile.resolve()),
                "relative_save": "save games/seed.ck3",
                "absolute_save": str(seed_source_save.resolve()),
                "bytes": seed_source_stat.st_size,
                "sha256": capture.isolated.sha256_file(seed_source_save),
                "last_write_time_utc": "2026-08-31T00:00:00Z",
                "last_write_time_ns": seed_source_stat.st_mtime_ns,
            },
            "provenance": {
                "source_run": str(seed_source_run.resolve()),
                "source_report_sha256": capture.isolated.sha256_file(
                    seed_source_report_path
                ),
                "source_evidence_index_sha256": capture.isolated.sha256_file(
                    seed_source_index_path
                ),
                "source_git_commit": "f" * 40,
                "real_character_proof": (
                    "typed save-checkpoint binds han_6875 to CharacterID 9001"
                ),
                "limitations": [
                    "synthetic fixture records source-tree provenance only"
                ],
            },
            "runtime": {
                "game_version": capture.EXPECTED_GAME_VERSION,
                "executable_sha256": capture.EXPECTED_EXE_SHA256,
                "enabled_mods": seed_enabled_mods,
                "source_product_tree_sha256": seed_product_tree,
                "source_fixture_tree_sha256": seed_fixture_tree,
            },
            "saved_state": {
                "date_raw": 777,
                "played_character_id": 9001,
                "player_history_id": capture.PHASE2_SEED_PLAYER_HISTORY_ID,
                "played_character_alive": True,
                "paused_on_load": True,
                "map_ready": True,
            },
            "install": {
                "continue_save_relative_path": "save games/autosave.ck3",
                "last_save_relative_path": "last_save.ck3",
                "launch_mode": "native_session_continue_last_save",
            },
            "domain_query_matrix": seed_domain_query_matrix,
        }
        ready_seed_path = temporary_root / "ready-seed-contract.json"
        ready_seed_path.write_text(
            json.dumps(ready_seed_contract), encoding="utf-8"
        )
        assert capture.preflight_phase2_seed_contract(ready_seed_path) == (
            ready_seed_contract
        )
        with (
            mock.patch.object(
                capture,
                "bootstrap_userdir",
                return_value={"seed": "bootstrap"},
            ) as seed_preflight_bootstrap,
            mock.patch.object(
                capture,
                "install_phase2_seed",
                return_value={"result": "GREEN"},
            ) as seed_preflight_install,
            mock.patch.object(
                capture.isolated,
                "installed_game_version",
                return_value=capture.EXPECTED_GAME_VERSION,
            ),
            mock.patch.object(
                capture.isolated,
                "sha256_file",
                return_value=capture.EXPECTED_EXE_SHA256,
            ),
        ):
            assert capture.preflight_phase2_seed_contract(
                ready_seed_path,
                runtime_source=temporary_root,
            ) == ready_seed_contract
        assert seed_preflight_bootstrap.call_count == 1
        assert seed_preflight_bootstrap.call_args.args[1] == temporary_root
        assert seed_preflight_install.call_count == 1
        assert seed_preflight_install.call_args.kwargs[
            "observed_game_version"
        ] == capture.EXPECTED_GAME_VERSION
        assert seed_preflight_install.call_args.kwargs[
            "observed_executable_sha256"
        ] == capture.EXPECTED_EXE_SHA256

        seed_install_userdir = temporary_root / "seed-install-profile"
        seed_install_artifacts = temporary_root / "seed-install-artifacts"
        seed_install_userdir.mkdir()
        seed_install_artifacts.mkdir()
        seed_bootstrap = {
            "tree_sha256": {
                "product": "1" * 64,
                "fixture": "2" * 64,
            },
            "enabled_mods": ready_seed_contract["runtime"]["enabled_mods"],
        }
        seed_install = capture.install_phase2_seed(
            seed_install_userdir,
            seed_bootstrap,
            seed_install_artifacts,
            observed_game_version=capture.EXPECTED_GAME_VERSION,
            observed_executable_sha256=capture.EXPECTED_EXE_SHA256,
            contract_path=ready_seed_path,
        )
        assert seed_install["result"] == "GREEN"
        assert seed_install["failed_checks"] == []
        installed_autosave = seed_install_userdir / "save games" / "autosave.ck3"
        installed_last_save = seed_install_userdir / "last_save.ck3"
        assert installed_autosave.read_bytes() == seed_source_save.read_bytes()
        assert installed_last_save.read_bytes() == seed_source_save.read_bytes()
        assert seed_install["ocr_used"] is False
        assert seed_install["coordinates_used"] is False
        assert seed_install["lobby_used"] is False
        assert seed_install["test_decision_used"] is False
        assert seed_install["runtime_tree_policy"][
            "source_current_equality_required_for_install"
        ] is False
        assert seed_install["runtime_tree_policy"]["source"] != (
            seed_install["runtime_tree_policy"]["current"]
        )
        assert seed_install["checks"][
            "source_product_tree_provenance_matches"
        ] is True
        assert seed_install["checks"][
            "current_product_runtime_tree_available"
        ] is True

        invalid_ready_contract = copy.deepcopy(ready_seed_contract)
        invalid_ready_contract["blocker"] = "stale blocker"
        invalid_ready_path = temporary_root / "invalid-ready-seed-contract.json"
        invalid_ready_path.write_text(
            json.dumps(invalid_ready_contract), encoding="utf-8"
        )
        try:
            capture.load_phase2_seed_contract(invalid_ready_path)
        except capture.acceptance.RunnerError as error:
            assert "must not retain a blocker" in str(error)
        else:
            raise AssertionError("ready seed retained a contradictory blocker")

        uncaptured_ready_contract = copy.deepcopy(ready_seed_contract)
        uncaptured_ready_contract["domain_query_matrix"][
            "incident_owner_character_id"
        ] = None
        uncaptured_ready_path = temporary_root / "uncaptured-ready-seed.json"
        uncaptured_ready_path.write_text(
            json.dumps(uncaptured_ready_contract), encoding="utf-8"
        )
        try:
            capture.load_phase2_seed_contract(uncaptured_ready_path)
        except capture.acceptance.RunnerError as error:
            assert "not a captured CharacterID" in str(error)
        else:
            raise AssertionError("ready seed accepted an uncaptured selector")

        misbound_history_contract = copy.deepcopy(ready_seed_contract)
        misbound_history_contract["saved_state"]["player_history_id"] = (
            capture.EXPECTED_PLAYER_HISTORY_ID
        )
        misbound_history_path = temporary_root / "misbound-history-seed.json"
        misbound_history_path.write_text(
            json.dumps(misbound_history_contract), encoding="utf-8"
        )
        try:
            capture.load_phase2_seed_contract(misbound_history_path)
        except capture.acceptance.RunnerError as error:
            assert "saved-state identity is invalid" in str(error)
        else:
            raise AssertionError("phase-two seed accepted promo emperor history")

        dll = temporary_root / "bridge.dll"
        injector = temporary_root / "injector.exe"
        managed_executable = temporary_root / "ck3.exe"
        dll.write_bytes(b"zg361-title-navigation-dll")
        injector.write_bytes(b"zg361-title-navigation-injector")
        managed_executable.write_bytes(b"zg361-title-navigation-managed-executable")
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
                "CK3_EXE",
                managed_executable,
            ),
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

        class LoaderReadinessService:
            def __init__(
                self,
                *,
                owner_tid: object = 88,
                current_tid: object = 88,
                rng_owner_tid: object = 0,
            ) -> None:
                self.index = -1
                self.current_index = 0
                self.owner_tid = owner_tid
                self.current_tid = current_tid
                self.rng_owner_tid = rng_owner_tid

            def capabilities(self) -> dict[str, object]:
                self.index = min(self.index + 1, 2)
                self.current_index = self.index
                sequence = 10 + self.current_index
                pump_epochs = 100 + self.current_index
                return {
                    "mode": "native-headless",
                    "backend_id": "native-headless",
                    "headless": True,
                    "visual_fallback": False,
                    "transport_ready": True,
                    "snapshot": True,
                    "diagnostics": {
                        "connected": True,
                        "semantic_state_available": True,
                        "bridge_pid": 4321,
                        "connection_generation": 4,
                        "hello": {
                            "expected_ck3_version": "1.19.0.6",
                            "expected_ck3_sha256": (
                                capture.EXPECTED_EXE_SHA256
                            ),
                            "ck3_build_match": True,
                            "game_adapter_status": "ready",
                        },
                        "last_heartbeat": {
                            "pid": 4321,
                            "sequence": sequence,
                            "main_thread_query_mailbox_v1": {
                                "installed": True,
                                "stop": False,
                                "failure": 0,
                                "pump_epochs": pump_epochs,
                                "consecutive_verified": 9 + self.current_index,
                                "owner_tid": self.owner_tid,
                                "current_tid": self.current_tid,
                                "rng_owner_tid": self.rng_owner_tid,
                                "jomini_state": 0x1000,
                                "game_state": 0x2000,
                                "date_raw": 500,
                                "paused": True,
                                "stamp_read_success": True,
                                "executor_submission_enabled": True,
                                "ready": True,
                            },
                        },
                    },
                }

            def snapshot(self) -> dict[str, object]:
                return {
                    "snapshot_id": f"native:{20 + self.current_index}",
                    "revision": 30 + self.current_index,
                    "native_revision": 20 + self.current_index,
                    "date_raw": 500,
                    "paused": True,
                    "map_ready": False,
                    "local_player_id": -1,
                    "played_character": None,
                    "diagnostics": {
                        "bridge_pid": 4321,
                        "connection_generation": 4,
                    },
                }

        loader_artifacts = temporary_root / "loader-readiness"
        loader_artifacts.mkdir()
        loader_readiness = capture.native_loader_smoke_readiness(
            LoaderReadinessService(),
            loader_artifacts,
            tracked_ck3_pid=4321,
            timeout_s=1.0,
            stable_observations=3,
            poll_interval_s=0.0,
        )
        assert loader_readiness["result"] == "GREEN"
        assert loader_readiness["scope"] == (
            "exact_build_application_main_loader_smoke_only"
        )
        assert loader_readiness["stable_binding"][
            "stable_observation_count"
        ] == 3
        assert loader_readiness["stable_binding"]["map_ready"] is False
        assert loader_readiness["played_character_required"] is False
        assert loader_readiness["gameplay_green_claimed"] is False
        assert loader_readiness["checks"][
            "main_thread_identity_consistent"
        ] is True
        assert loader_readiness["last_capabilities"]["diagnostics"][
            "last_heartbeat"
        ]["main_thread_query_mailbox_v1"]["rng_owner_tid"] == 0
        persisted_loader_readiness = json.loads(
            (
                loader_artifacts / "01_loader_native_readiness.json"
            ).read_text(encoding="utf-8")
        )
        assert persisted_loader_readiness == loader_readiness

        mismatched_rng_artifacts = temporary_root / "loader-readiness-rng-mismatch"
        mismatched_rng_artifacts.mkdir()
        mismatched_rng_readiness = capture.native_loader_smoke_readiness(
            LoaderReadinessService(rng_owner_tid=89),
            mismatched_rng_artifacts,
            tracked_ck3_pid=4321,
            timeout_s=1.0,
            stable_observations=2,
            poll_interval_s=0.0,
        )
        assert mismatched_rng_readiness["result"] == "GREEN"
        assert mismatched_rng_readiness["checks"][
            "main_thread_identity_consistent"
        ] is True

        mismatched_thread_artifacts = (
            temporary_root / "loader-readiness-thread-mismatch"
        )
        mismatched_thread_artifacts.mkdir()
        try:
            capture.native_loader_smoke_readiness(
                LoaderReadinessService(current_tid=89),
                mismatched_thread_artifacts,
                tracked_ck3_pid=4321,
                timeout_s=0.001,
                stable_observations=2,
                poll_interval_s=0.0,
            )
        except capture.acceptance.RunnerError as error:
            assert "main_thread_identity_consistent" in str(error)
        else:
            raise AssertionError(
                "loader readiness accepted a mismatched application-main thread"
            )
        mismatched_thread_gate = json.loads(
            (
                mismatched_thread_artifacts
                / "01_loader_native_readiness.json"
            ).read_text(encoding="utf-8")
        )
        assert mismatched_thread_gate["result"] == "RED"
        assert mismatched_thread_gate["checks"][
            "main_thread_identity_consistent"
        ] is False

        def complete_phase2_capabilities() -> dict[str, object]:
            return {
                "mode": "native-headless",
                "backend_id": "native-headless",
                "visual_fallback": False,
                "snapshot": True,
                "wait_for_change": True,
                "bridge_capabilities": sorted(
                    set(capture.PHASE2_REQUIRED_BRIDGE_CAPABILITIES.values())
                ),
                "action_steps": sorted(
                    set(capture.PHASE2_REQUIRED_ACTION_STEPS.values())
                ),
                **{
                    flag: True
                    for flag in capture.PHASE2_REQUIRED_QUERY_FLAGS.values()
                },
                "checkpoint_materialization": {"configured": True},
                "native_session_control": {"configured": True},
                "diagnostics": {
                    "connected": True,
                    "bridge_pid": 4321,
                    "connection_generation": 4,
                },
            }

        class Phase2CapabilityService:
            def __init__(self, capabilities: dict[str, object]) -> None:
                self.value = capabilities

            def capabilities(self) -> dict[str, object]:
                return copy.deepcopy(self.value)

        phase2_capability_artifacts = (
            temporary_root / "phase2-provider-profile-green"
        )
        phase2_capability_artifacts.mkdir()
        phase2_capability_green = capture.phase2_runtime_capability_preflight(
            Phase2CapabilityService(complete_phase2_capabilities()),
            phase2_capability_artifacts,
            tracked_ck3_pid=4321,
            managed_restore_supervisor=True,
        )
        assert phase2_capability_green["result"] == "GREEN"
        phase2_persisted_green = json.loads(
            (
                phase2_capability_artifacts
                / "02_phase2_mcp_capabilities.json"
            ).read_text(encoding="utf-8")
        )
        assert phase2_persisted_green == phase2_capability_green
        assert phase2_persisted_green["mcp_only"] is True
        assert phase2_persisted_green["legacy_scenario_used"] is False
        assert phase2_persisted_green["missing_requirements"] == []
        assert capture.PHASE2_UNFROZEN_REQUIREMENTS == {}
        assert (
            capture.PHASE2_REQUIRED_BRIDGE_CAPABILITIES[
                "workforce_collective_snapshot"
            ]
            == "game.command.query-zhongguo-workforce-collective-snapshot-v1"
        )
        assert (
            capture.PHASE2_REQUIRED_QUERY_FLAGS[
                "workforce_collective_snapshot"
            ]
            == "zhongguo_workforce_collective_snapshot_v1_query_supported"
        )
        assert (
            capture.PHASE2_REQUIRED_BRIDGE_CAPABILITIES[
                "ai_owned_case_snapshot"
            ]
            == "game.command.query-zhongguo-ai-owned-case-snapshot-v1"
        )
        assert (
            capture.PHASE2_REQUIRED_QUERY_FLAGS["ai_owned_case_snapshot"]
            == "zhongguo_ai_owned_case_snapshot_v1_query_supported"
        )
        assert (
            capture.PHASE2_REQUIRED_BRIDGE_CAPABILITIES[
                "manager_governance_snapshot"
            ]
            == "game.command.query-zhongguo-manager-governance-snapshot-v1"
        )
        assert (
            capture.PHASE2_REQUIRED_QUERY_FLAGS[
                "manager_governance_snapshot"
            ]
            == "zhongguo_manager_governance_snapshot_v1_query_supported"
        )
        assert "workforce_collective_snapshot_and_three_cycle" not in (
            capture.PHASE2_UNFROZEN_REQUIREMENTS
        )
        assert "ai_owned_case_snapshot" not in (
            capture.PHASE2_UNFROZEN_REQUIREMENTS
        )
        assert capture.PHASE2_REQUIRED_BRIDGE_CAPABILITIES[
            "scoreboard_state_acl"
        ] == "game.command.query-zhongguo-scoreboard-state-v1"
        assert capture.PHASE2_REQUIRED_QUERY_FLAGS[
            "scoreboard_state_acl"
        ] == "zhongguo_scoreboard_state_v1_query_supported"
        assert {
            row["label"]
            for row in phase2_persisted_green["missing_requirements"]
            if row["kind"] == "runner_not_wired"
        } == set(capture.PHASE2_PENDING_RUNNER_REQUIREMENTS)

        for label, required_capability in (
            capture.PHASE2_REQUIRED_BRIDGE_CAPABILITIES.items()
        ):
            missing_capabilities = complete_phase2_capabilities()
            missing_capabilities["bridge_capabilities"].remove(
                required_capability
            )
            missing_dir = temporary_root / f"phase2-missing-capability-{label}"
            missing_dir.mkdir()
            try:
                capture.phase2_runtime_capability_preflight(
                    Phase2CapabilityService(missing_capabilities),
                    missing_dir,
                    tracked_ck3_pid=4321,
                    managed_restore_supervisor=True,
                )
            except capture.acceptance.RunnerError as error:
                assert "MCP capability RED" in str(error)
            else:
                raise AssertionError(
                    f"phase-two preflight accepted missing {label}"
                )
            persisted_missing = json.loads(
                (missing_dir / "02_phase2_mcp_capabilities.json").read_text(
                    encoding="utf-8"
                )
            )
            assert persisted_missing["result"] == "RED"
            assert any(
                row["label"] == label
                and row["value"] == required_capability
                for row in persisted_missing["missing_requirements"]
            )

        for label, required_flag in capture.PHASE2_REQUIRED_QUERY_FLAGS.items():
            missing_flag_capabilities = complete_phase2_capabilities()
            missing_flag_capabilities[required_flag] = False
            missing_dir = temporary_root / f"phase2-missing-flag-{label}"
            missing_dir.mkdir()
            try:
                capture.phase2_runtime_capability_preflight(
                    Phase2CapabilityService(missing_flag_capabilities),
                    missing_dir,
                    tracked_ck3_pid=4321,
                    managed_restore_supervisor=True,
                )
            except capture.acceptance.RunnerError as error:
                assert "MCP capability RED" in str(error)
            else:
                raise AssertionError(
                    f"phase-two preflight accepted false {required_flag}"
                )

        for label, required_step in capture.PHASE2_REQUIRED_ACTION_STEPS.items():
            missing_step_capabilities = complete_phase2_capabilities()
            missing_step_capabilities["action_steps"].remove(required_step)
            missing_dir = temporary_root / f"phase2-missing-step-{label}"
            missing_dir.mkdir()
            try:
                capture.phase2_runtime_capability_preflight(
                    Phase2CapabilityService(missing_step_capabilities),
                    missing_dir,
                    tracked_ck3_pid=4321,
                    managed_restore_supervisor=True,
                )
            except capture.acceptance.RunnerError as error:
                assert "MCP capability RED" in str(error)
            else:
                raise AssertionError(
                    f"phase-two preflight accepted missing {required_step}"
                )
            persisted_missing = json.loads(
                (missing_dir / "02_phase2_mcp_capabilities.json").read_text(
                    encoding="utf-8"
                )
            )
            assert any(
                row["kind"] == "materialized_action_step"
                and row["label"] == label
                and row["value"] == required_step
                for row in persisted_missing["missing_requirements"]
            )

        runtime_red_cases = {
            "native_headless_mode": lambda value: value.__setitem__(
                "mode", "visual"
            ),
            "native_headless_backend": lambda value: value.__setitem__(
                "backend_id", "visual"
            ),
            "visual_fallback_disabled": lambda value: value.__setitem__(
                "visual_fallback", True
            ),
            "snapshot_available": lambda value: value.__setitem__(
                "snapshot", False
            ),
            "wait_for_change_available": lambda value: value.__setitem__(
                "wait_for_change", False
            ),
            "checkpoint_materialization_configured": lambda value: value[
                "checkpoint_materialization"
            ].__setitem__("configured", False),
            "restore_lifecycle_configured": lambda value: value[
                "native_session_control"
            ].__setitem__("configured", False),
            "connected": lambda value: value["diagnostics"].__setitem__(
                "connected", False
            ),
            "tracked_ck3_pid_matches_bridge": lambda value: value[
                "diagnostics"
            ].__setitem__("bridge_pid", 9876),
            "positive_connection_generation": lambda value: value[
                "diagnostics"
            ].__setitem__("connection_generation", 0),
        }
        for label, mutate in runtime_red_cases.items():
            missing_runtime = complete_phase2_capabilities()
            mutate(missing_runtime)
            missing_dir = temporary_root / f"phase2-runtime-red-{label}"
            missing_dir.mkdir()
            try:
                capture.phase2_runtime_capability_preflight(
                    Phase2CapabilityService(missing_runtime),
                    missing_dir,
                    tracked_ck3_pid=4321,
                    managed_restore_supervisor=True,
                )
            except capture.acceptance.RunnerError as error:
                assert "MCP capability RED" in str(error)
            else:
                raise AssertionError(
                    f"phase-two preflight accepted runtime RED {label}"
                )
            persisted_missing = json.loads(
                (missing_dir / "02_phase2_mcp_capabilities.json").read_text(
                    encoding="utf-8"
                )
            )
            assert any(
                row["kind"] == "runtime_check" and row["label"] == label
                for row in persisted_missing["missing_requirements"]
            )

        missing_supervisor_dir = temporary_root / "phase2-runtime-red-supervisor"
        missing_supervisor_dir.mkdir()
        try:
            capture.phase2_runtime_capability_preflight(
                Phase2CapabilityService(complete_phase2_capabilities()),
                missing_supervisor_dir,
                tracked_ck3_pid=4321,
                managed_restore_supervisor=False,
            )
        except capture.acceptance.RunnerError as error:
            assert "MCP capability RED" in str(error)
        else:
            raise AssertionError(
                "phase-two preflight accepted a missing restore supervisor"
            )
        missing_supervisor = json.loads(
            (
                missing_supervisor_dir / "02_phase2_mcp_capabilities.json"
            ).read_text(encoding="utf-8")
        )
        assert any(
            row["kind"] == "runtime_check"
            and row["label"] == "restore_lifecycle_supervisor_running"
            for row in missing_supervisor["missing_requirements"]
        )

        def phase2_snapshot(
            *, pid: int, generation: int, revision: int, player: int = 9001
        ) -> dict[str, object]:
            return {
                "snapshot_id": f"phase2-{pid}-{generation}-{revision}",
                "revision": revision,
                "native_revision": revision + 100,
                "date_raw": 777,
                "paused": True,
                "map_ready": True,
                "played_character": {"character_id": player, "alive": True},
                "diagnostics": {
                    "connected": True,
                    "bridge_pid": pid,
                    "connection_generation": generation,
                },
            }

        def phase2_loaded_feature_manifest(
            snapshot: dict[str, object],
            *,
            merit_admin: bool = True,
        ) -> dict[str, object]:
            return {
                "status": "available",
                "loaded_feature_manifest_ready": True,
                "binding": {
                    "snapshot_id": snapshot["snapshot_id"],
                    "revision": snapshot["revision"],
                    "native_revision": snapshot["native_revision"],
                    "date_raw": snapshot["date_raw"],
                },
                "effective_feature_flags": {
                    "status": "available",
                    "items": [
                        {"key": "all_under_heaven", "enabled": True},
                        {"key": "merit_admin", "enabled": merit_admin},
                    ],
                },
                "script_dlc_keys": {
                    "status": "available",
                    "keys": ["All Under Heaven"],
                },
            }

        seed_loaded_artifacts = temporary_root / "phase2-seed-loaded-green"
        seed_loaded_artifacts.mkdir()
        loaded_snapshot = phase2_snapshot(pid=4321, generation=4, revision=10)
        loaded_seed = capture.prove_phase2_loaded_seed(
            loaded_snapshot,
            ready_seed_contract,
            seed_loaded_artifacts,
            loaded_feature_manifest=phase2_loaded_feature_manifest(
                loaded_snapshot
            ),
        )
        assert loaded_seed["result"] == "GREEN"
        assert loaded_seed["observed"]["date_raw"] == 777
        assert loaded_seed["observed"]["player_character_id"] == 9001
        wrong_seed_artifacts = temporary_root / "phase2-seed-loaded-red"
        wrong_seed_artifacts.mkdir()
        wrong_seed_snapshot = phase2_snapshot(
            pid=4321, generation=4, revision=10
        )
        wrong_seed_snapshot["date_raw"] = 778
        try:
            capture.prove_phase2_loaded_seed(
                wrong_seed_snapshot,
                ready_seed_contract,
                wrong_seed_artifacts,
                loaded_feature_manifest=phase2_loaded_feature_manifest(
                    wrong_seed_snapshot
                ),
            )
        except capture.acceptance.RunnerError as error:
            assert "date_raw_matches_seed" in str(error)
        else:
            raise AssertionError("wrong loaded phase-two seed was accepted")
        persisted_wrong_seed = json.loads(
            (wrong_seed_artifacts / "04_phase2_seed_loaded.json").read_text(
                encoding="utf-8"
            )
        )
        assert persisted_wrong_seed["result"] == "RED"
        assert persisted_wrong_seed["checks"]["date_raw_matches_seed"] is False
        wrong_player_artifacts = temporary_root / "phase2-seed-player-red"
        wrong_player_artifacts.mkdir()
        try:
            wrong_player_snapshot = phase2_snapshot(
                pid=4321,
                generation=4,
                revision=10,
                player=9002,
            )
            capture.prove_phase2_loaded_seed(
                wrong_player_snapshot,
                ready_seed_contract,
                wrong_player_artifacts,
                loaded_feature_manifest=phase2_loaded_feature_manifest(
                    wrong_player_snapshot
                ),
            )
        except capture.acceptance.RunnerError as error:
            assert "played_character_matches_seed" in str(error)
        else:
            raise AssertionError("wrong phase-two seed player was accepted")

        class Phase2RestoreService:
            def __init__(
                self,
                *,
                second_pid: int = 5432,
                second_generation: int = 5,
                restored_sha256: str = "a" * 64,
                restored_player: int = 9001,
                action_revision: int | None = None,
                action_date_raw: int = 777,
            ) -> None:
                self.second_pid = second_pid
                self.second_generation = second_generation
                self.restored_sha256 = restored_sha256
                self.snapshots = [
                    phase2_snapshot(pid=4321, generation=4, revision=10),
                    phase2_snapshot(pid=4321, generation=4, revision=11),
                ]
                if action_revision is not None:
                    action_snapshot = phase2_snapshot(
                        pid=4321,
                        generation=4,
                        revision=action_revision,
                    )
                    action_snapshot["date_raw"] = action_date_raw
                    self.snapshots.append(action_snapshot)
                self.snapshots.append(
                    phase2_snapshot(
                        pid=second_pid,
                        generation=second_generation,
                        revision=20,
                        player=restored_player,
                    )
                )
                self.expected_restore_revision = action_revision or 11
                self.snapshot_index = 0
                self.capabilities_index = 0

            def snapshot(self) -> dict[str, object]:
                value = self.snapshots[self.snapshot_index]
                self.snapshot_index += 1
                return copy.deepcopy(value)

            def save_checkpoint(
                self, *, expected_revision: int
            ) -> dict[str, object]:
                assert expected_revision == 10
                return {
                    "accepted": True,
                    "checkpoint": {
                        "status": "saved",
                        "size": 123456,
                        "sha256": "a" * 64,
                        "date_raw": 777,
                    },
                }

            def capabilities(self) -> dict[str, object]:
                self.capabilities_index += 1
                if self.capabilities_index == 1:
                    return {"action_steps": ["restore-checkpoint"]}
                return {
                    "diagnostics": {
                        "connected": True,
                        "bridge_pid": self.second_pid,
                        "connection_generation": self.second_generation,
                    }
                }

            def restore_checkpoint(
                self, *, expected_revision: int
            ) -> dict[str, object]:
                assert expected_revision == self.expected_restore_revision
                return {
                    "accepted": True,
                    "status": "restored",
                    "source": "native-session-lifecycle-queue",
                    "checkpoint": {
                        "status": "restored",
                        "size": 123456,
                        "sha256": self.restored_sha256,
                    },
                    "restored_date": {"date_raw": 777},
                    "lifecycle": {
                        "previous_pid": 4321,
                        "pid": self.second_pid,
                        "previous_connection_generation": 4,
                        "connection_generation": self.second_generation,
                        "lifecycle_intent": "restore",
                        "request_id": "phase2-restore-1",
                    },
                }

        lineage_artifacts = temporary_root / "phase2-two-pid-lineage-green"
        lineage_artifacts.mkdir()
        lineage = capture.run_phase2_save_restore_lineage(
            Phase2RestoreService(),
            lineage_artifacts,
            tracked_ck3_pid=4321,
        )
        assert lineage["result"] == "GREEN"
        assert lineage["pid_lineage"] == [4321, 5432]
        assert lineage["connection_generation_lineage"] == [4, 5]
        assert lineage["two_pid_lineage_proven"] is True
        assert json.loads(
            (
                lineage_artifacts / "06_phase2_save_restore_lineage.json"
            ).read_text(encoding="utf-8")
        ) == lineage

        checkpointed_action_evidence = {
            "schema_version": 1,
            "cell": "zg361.phase2.b2.pip-response-action",
            "result": "GREEN",
            "selection_submission": {
                "accepted": True,
                "status": "submitted",
                "event_instance_id": 601,
                "option_number": 1,
            },
            "postcondition_query_green": True,
        }
        checkpointed_action_calls: list[str] = []

        def checkpointed_action() -> dict[str, object]:
            checkpointed_action_calls.append("b2-accept")
            return copy.deepcopy(checkpointed_action_evidence)

        action_lineage_artifacts = (
            temporary_root / "phase2-checkpointed-action-lineage-green"
        )
        action_lineage_artifacts.mkdir()
        action_lineage = capture.run_phase2_save_restore_lineage(
            Phase2RestoreService(action_revision=14),
            action_lineage_artifacts,
            tracked_ck3_pid=4321,
            checkpointed_gameplay_action=checkpointed_action,
        )
        assert checkpointed_action_calls == ["b2-accept"]
        assert action_lineage["result"] == "GREEN"
        assert action_lineage["before_restore"]["revision"] == 14
        assert action_lineage["checkpointed_gameplay_action"] == (
            checkpointed_action_evidence
        )
        assert action_lineage["checkpointed_gameplay_action_green"] is True
        assert action_lineage["checks"]["action_stayed_on_first_pid"] is True
        assert action_lineage["checks"]["action_date_contract_matches"] is True

        timeline_action_evidence = {
            "schema_version": 1,
            "result": "GREEN",
            "timeline_advance_expected": True,
            "ai_owned_case_gameplay_action_cell": {
                "result": "GREEN",
                "background_business_complete": True,
            },
        }
        timeline_lineage_artifacts = (
            temporary_root / "phase2-timeline-action-lineage-green"
        )
        timeline_lineage_artifacts.mkdir()
        timeline_lineage = capture.run_phase2_save_restore_lineage(
            Phase2RestoreService(
                action_revision=15,
                action_date_raw=801,
            ),
            timeline_lineage_artifacts,
            tracked_ck3_pid=4321,
            checkpointed_gameplay_action=lambda: copy.deepcopy(
                timeline_action_evidence
            ),
        )
        assert timeline_lineage["before_restore"]["date_raw"] == 801
        assert timeline_lineage["after_restore"]["date_raw"] == 777
        assert timeline_lineage["checks"]["action_date_not_before_checkpoint"]
        assert timeline_lineage["checks"]["action_date_contract_matches"]

        restored_red_artifacts = (
            temporary_root / "phase2-checkpointed-action-red-restored"
        )
        restored_red_artifacts.mkdir()

        def checkpointed_action_red() -> dict[str, object]:
            raise capture.acceptance.RunnerError(
                "fixture checkpointed gameplay action RED"
            )

        try:
            capture.run_phase2_save_restore_lineage(
                Phase2RestoreService(
                    action_revision=16,
                    action_date_raw=801,
                ),
                restored_red_artifacts,
                tracked_ck3_pid=4321,
                checkpointed_gameplay_action=checkpointed_action_red,
            )
        except capture.acceptance.RunnerError as error:
            assert "fixture checkpointed gameplay action RED" in str(error)
        else:
            raise AssertionError(
                "checkpointed action RED did not propagate after restore"
            )
        restored_red_lineage = json.loads(
            (
                restored_red_artifacts
                / "06_phase2_save_restore_lineage.json"
            ).read_text(encoding="utf-8")
        )
        assert restored_red_lineage["result"] == "GREEN"
        assert restored_red_lineage[
            "restore_completed_after_action_failure"
        ] is True
        assert restored_red_lineage["restore_result"]["status"] == "restored"
        assert restored_red_lineage["two_pid_lineage_proven"] is True
        assert restored_red_lineage[
            "checkpointed_gameplay_action_green"
        ] is False

        lineage_red_cases = {
            "second_pid_is_distinct": {"second_pid": 4321},
            "connection_generation_advanced": {"second_generation": 4},
            "checkpoint_sha256_preserved": {"restored_sha256": "b" * 64},
            "player_identity_restored": {"restored_player": 9002},
        }
        for failed_check, kwargs in lineage_red_cases.items():
            red_dir = temporary_root / f"phase2-lineage-red-{failed_check}"
            red_dir.mkdir()
            try:
                capture.run_phase2_save_restore_lineage(
                    Phase2RestoreService(**kwargs),
                    red_dir,
                    tracked_ck3_pid=4321,
                )
            except capture.acceptance.RunnerError as error:
                assert "save/restore lineage RED" in str(error)
                assert failed_check in str(error)
            else:
                raise AssertionError(
                    f"phase-two lineage accepted {failed_check} failure"
                )
            persisted_red = json.loads(
                (red_dir / "06_phase2_save_restore_lineage.json").read_text(
                    encoding="utf-8"
                )
            )
            assert persisted_red["result"] == "RED"
            assert persisted_red["checks"][failed_check] is False

        class Phase2B2PromptService:
            def __init__(self, event_key: str = "zg361b2.40") -> None:
                self.state = "baseline"
                self.event_key = event_key
                self.calls: list[tuple[object, ...]] = []

            def snapshot(self) -> dict[str, object]:
                if self.state == "baseline":
                    value = phase2_snapshot(
                        pid=4321, generation=4, revision=30
                    )
                    value["speed"] = 0
                    return value
                if self.state == "speed-one":
                    value = phase2_snapshot(
                        pid=4321, generation=4, revision=31
                    )
                    value["speed"] = 1
                    return value
                value = phase2_snapshot(
                    pid=4321, generation=4, revision=32
                )
                value["date_raw"] = 779
                value["speed"] = 1
                value["active_event"] = {
                    "instance_id": 601,
                    "option_count": 3,
                }
                self.state = "event"
                return value

            def execute_step(
                self, step: str, *, expected_revision: int
            ) -> dict[str, object]:
                self.calls.append((step, expected_revision))
                if step == "set-speed-1":
                    assert self.state == "baseline"
                    assert expected_revision == 30
                    self.state = "speed-one"
                elif step == "resume-map":
                    assert self.state == "speed-one"
                    assert expected_revision == 31
                    self.state = "resumed"
                else:
                    raise AssertionError(f"unexpected step: {step}")
                return {
                    "accepted": True,
                    "status": "submitted",
                    "step": step,
                }

            def query_current_event_window_context_v1(
                self, event_instance_id: int, *, expected_revision: int
            ) -> dict[str, object]:
                assert event_instance_id == 601
                assert expected_revision == 32
                self.calls.append(("current-event", event_instance_id))
                return {
                    "status": "available",
                    "current_event_window_context": {
                        "event_definition_key": self.event_key,
                        "readiness": {
                            "event_definition_identity_ready": True,
                        },
                    },
                }

        prompt_baseline_snapshot = phase2_snapshot(
            pid=4321, generation=4, revision=30
        )
        prompt_baseline_binding = capture._phase2_paused_binding(
            prompt_baseline_snapshot,
            label="test B2 prompt baseline",
        )
        prompt_artifacts = temporary_root / "phase2-b2-prompt-green"
        prompt_artifacts.mkdir()
        prompt_service = Phase2B2PromptService()
        prompt_snapshot = capture.wait_for_phase2_b2_pip_prompt(
            prompt_service,
            prompt_artifacts,
            baseline_binding=prompt_baseline_binding,
            timeout_s=0.1,
            poll_interval_s=0.0,
        )
        assert prompt_snapshot["active_event"]["instance_id"] == 601
        assert prompt_service.calls == [
            ("set-speed-1", 30),
            ("resume-map", 31),
            ("current-event", 601),
        ]
        prompt_evidence = json.loads(
            (
                prompt_artifacts
                / "05_phase2_b2_pip_prompt_readiness.json"
            ).read_text(encoding="utf-8")
        )
        assert prompt_evidence["result"] == "GREEN"
        assert prompt_evidence["event_identity"][
            "event_definition_key"
        ] == "zg361b2.40"
        assert prompt_evidence["ocr_used"] is False
        assert prompt_evidence["coordinates_used"] is False

        wrong_prompt_artifacts = temporary_root / "phase2-b2-prompt-red"
        wrong_prompt_artifacts.mkdir()
        try:
            capture.wait_for_phase2_b2_pip_prompt(
                Phase2B2PromptService("unrelated.999"),
                wrong_prompt_artifacts,
                baseline_binding=prompt_baseline_binding,
                timeout_s=0.1,
                poll_interval_s=0.0,
            )
        except capture.acceptance.RunnerError as error:
            assert "unexpected real event" in str(error)
        else:
            raise AssertionError("B2 readiness accepted an unrelated event")
        wrong_prompt_evidence = json.loads(
            (
                wrong_prompt_artifacts
                / "05_phase2_b2_pip_prompt_readiness.json"
            ).read_text(encoding="utf-8")
        )
        assert wrong_prompt_evidence["result"] == "RED"
        assert "unrelated.999" in wrong_prompt_evidence["failure_reason"]

        def rebind_domain_response(
            value: dict[str, object],
            *,
            binding: dict[str, int | str],
            nonce: str,
            requested_owner: int,
            old_player: int,
            old_owner: int,
            old_subject: int | None = None,
            subject_character_id: int | None = None,
            retain_unavailable_owner_binding: bool = False,
            profile: str | None = None,
        ) -> dict[str, object]:
            response = copy.deepcopy(value)
            player = int(binding["player_character_id"])
            target_subject = (
                player
                if subject_character_id is None
                else subject_character_id
            )
            source_subject = old_player if old_subject is None else old_subject

            def rewrite_typed_character_ids(
                node: object, parent_key: str | None = None
            ) -> None:
                if isinstance(node, list):
                    for child in node:
                        rewrite_typed_character_ids(child, parent_key)
                    return
                if not isinstance(node, dict):
                    return
                if set(node) == {"status", "value", "unavailable_reason"}:
                    if node.get("status") != "available":
                        return
                    if parent_key in {
                        "subject_character_id",
                        "consumed_subject_character_id",
                    } and node.get("value") == source_subject:
                        node["value"] = target_subject
                    if parent_key in {
                        "owner_character_id",
                        "budget_owner_character_id",
                        "consumed_owner_character_id",
                        "subject_immediate_liege_character_id",
                    } and node.get("value") == old_owner:
                        node["value"] = requested_owner
                    return
                for key, child in node.items():
                    rewrite_typed_character_ids(child, key)

            rewrite_typed_character_ids(response)
            response.update(
                {
                    "request_nonce": nonce,
                    "snapshot_revision": binding["native_revision"],
                    "date_raw": binding["date_raw"],
                    "paused": True,
                    "player_character_id": player,
                    "subject_character_id": target_subject,
                    "requested_owner_character_id": requested_owner,
                }
            )
            if profile is not None:
                response["profile"] = profile
            source = response["source"]
            assert isinstance(source, dict)
            source.update(
                {
                    "connection_generation": binding[
                        "connection_generation"
                    ],
                    "snapshot_id": binding["snapshot_id"],
                    "revision": binding["revision"],
                    "native_revision": binding["native_revision"],
                    "date_raw": binding["date_raw"],
                    "paused": True,
                    "player_character_id": player,
                }
            )
            response_binding = response["binding"]
            assert isinstance(response_binding, dict)
            response_binding.update(
                {
                    "request_nonce": nonce,
                    "snapshot_id": binding["snapshot_id"],
                    "revision": binding["revision"],
                    "native_revision": binding["native_revision"],
                    "connection_generation": binding[
                        "connection_generation"
                    ],
                    "date_raw": binding["date_raw"],
                    "paused": True,
                    "player_character_id": player,
                    "subject_character_id": target_subject,
                    "owner_character_id": (
                        requested_owner
                        if response.get("status") == "available"
                        or retain_unavailable_owner_binding
                        else None
                    ),
                    "expected_revision": binding["revision"],
                }
            )
            if profile is not None:
                response_binding["profile"] = profile
            return response

        def incident_acl_frame(profile: str) -> dict[str, object]:
            frame = incident_snapshot_fixture.na_frame(profile)
            frame["status"] = "unavailable"
            frame["unavailable_reason"] = "owner_filter_mismatch"
            frame["probe"] = {
                key: incident_snapshot_fixture.unavailable(
                    "snapshot_unavailable"
                )
                for key in incident_snapshot_fixture.PROBE_KEYS
            }
            frame["resources"] = {
                key: incident_snapshot_fixture.unavailable(
                    "snapshot_unavailable"
                )
                for key in incident_snapshot_fixture.RESOURCE_KEYS
            }
            frame["terminal"] = {
                "kind": "unavailable",
                "na": None,
                "incident": None,
            }
            frame["kpi"] = {
                "disposition": "unavailable",
                **{
                    key: incident_snapshot_fixture.unavailable(
                        "snapshot_unavailable"
                    )
                    for key in incident_snapshot_fixture.KPI_KEYS
                },
            }
            frame["readiness"] = {
                key: key == "same_frame_ready"
                for key in frame["readiness"]
            }
            return frame

        pre_domain_snapshot = phase2_snapshot(
            pid=4321, generation=4, revision=10
        )
        post_domain_snapshot = phase2_snapshot(
            pid=5432, generation=5, revision=20
        )
        pre_domain_binding = capture._phase2_paused_binding(
            pre_domain_snapshot, label="test pre-domain binding"
        )
        post_domain_binding = capture._phase2_paused_binding(
            post_domain_snapshot, label="test post-domain binding"
        )
        domain_owner_contract = {
            "b2_pip_owner_character_id": 9100,
            "incident_owner_character_id": 9200,
            "workforce_owner_character_id": 9300,
            "ai_owned_case_owner_character_id": 9400,
            "ai_owned_case_subject_character_id": 9500,
        }
        domain_seed = {
            "domain_query_matrix": {
                "schema_version": 1,
                **domain_owner_contract,
            }
        }
        assert capture._phase2_domain_query_contract(
            domain_seed,
            player_character_id=9001,
        ) == domain_owner_contract
        incomplete_domain_seed = copy.deepcopy(domain_seed)
        incomplete_domain_seed["domain_query_matrix"].pop(
            "ai_owned_case_subject_character_id"
        )
        try:
            capture._phase2_domain_query_contract(
                incomplete_domain_seed,
                player_character_id=9001,
            )
        except capture.acceptance.RunnerError as error:
            assert "Workforce and AI-owned-case selectors" in str(error)
        else:
            raise AssertionError(
                "phase-two domain contract accepted a missing AI subject"
            )
        player_owned_domain_seed = copy.deepcopy(domain_seed)
        player_owned_domain_seed["domain_query_matrix"][
            "workforce_owner_character_id"
        ] = 9001
        try:
            capture._phase2_domain_query_contract(
                player_owned_domain_seed,
                player_character_id=9001,
            )
        except capture.acceptance.RunnerError as error:
            assert "must not be the played CharacterID" in str(error)
        else:
            raise AssertionError(
                "phase-two domain contract accepted player as Workforce owner"
            )
        self_owned_ai_seed = copy.deepcopy(domain_seed)
        self_owned_ai_seed["domain_query_matrix"][
            "ai_owned_case_subject_character_id"
        ] = self_owned_ai_seed["domain_query_matrix"][
            "ai_owned_case_owner_character_id"
        ]
        try:
            capture._phase2_domain_query_contract(
                self_owned_ai_seed,
                player_character_id=9001,
            )
        except capture.acceptance.RunnerError as error:
            assert "AI-owned owner and subject must differ" in str(error)
        else:
            raise AssertionError(
                "phase-two domain contract accepted identical AI owner/subject"
            )

        class Phase2DomainService:
            def __init__(self) -> None:
                self.binding = pre_domain_binding
                self.calls: list[tuple[object, ...]] = []
                self.missing_b2_flag = False
                self.partial_b2 = False
                self.partial_workforce = False
                self.partial_ai_owned = False

            def capabilities(self) -> dict[str, object]:
                return {
                    "bridge_capabilities": [
                        capture.QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY,
                        capture.QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
                        capture.QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY,
                        capture.QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY,
                        capture.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
                        "game.command.select-event-option-N",
                    ],
                    "action_steps": [
                        "save-checkpoint",
                        "restore-checkpoint",
                    ],
                    "zhongguo_b2_pip_snapshot_v1_query_supported": (
                        not self.missing_b2_flag
                    ),
                    "zhongguo_incident_snapshot_v1_query_supported": True,
                    "zhongguo_workforce_collective_snapshot_v1_query_supported": True,
                    "zhongguo_ai_owned_case_snapshot_v1_query_supported": True,
                }

            def save_checkpoint(self, **_kwargs: object) -> dict[str, object]:
                raise AssertionError("static preflight unexpectedly saved")

            def restore_checkpoint(self, **_kwargs: object) -> dict[str, object]:
                raise AssertionError("static preflight unexpectedly restored")

            def query_current_event_window_context_v1(
                self, *_args: object, **_kwargs: object
            ) -> dict[str, object]:
                raise AssertionError("static preflight unexpectedly queried")

            def select_event_option(
                self, *_args: object, **_kwargs: object
            ) -> dict[str, object]:
                raise AssertionError("static preflight unexpectedly selected")

            def snapshot(self) -> dict[str, object]:
                return {
                    "snapshot_id": self.binding["snapshot_id"],
                    "revision": self.binding["revision"],
                    "native_revision": self.binding["native_revision"],
                    "date_raw": self.binding["date_raw"],
                    "paused": True,
                    "map_ready": True,
                    "played_character": {
                        "character_id": self.binding["player_character_id"],
                        "alive": True,
                    },
                    "diagnostics": {
                        "connected": True,
                        "bridge_pid": self.binding["bridge_pid"],
                        "connection_generation": self.binding[
                            "connection_generation"
                        ],
                    },
                }

            def query_loaded_feature_manifest_v1(
                self, *, expected_revision: int
            ) -> dict[str, object]:
                assert expected_revision == int(self.binding["revision"])
                self.calls.append(("manifest", expected_revision))
                return phase2_loaded_feature_manifest(self.snapshot())

            def query_zhongguo_b2_pip_snapshot_v1(
                self,
                nonce: str,
                *,
                expected_revision: int,
                owner_character_id: int,
            ) -> dict[str, object]:
                assert expected_revision == int(self.binding["revision"])
                self.calls.append(
                    (
                        "b2",
                        int(self.binding["connection_generation"]),
                        owner_character_id,
                    )
                )
                actual_owner = domain_owner_contract[
                    "b2_pip_owner_character_id"
                ]
                if owner_character_id == actual_owner:
                    value = b2_snapshot_fixture._response(
                        b2_snapshot_fixture._pending_frame()
                    )
                else:
                    value = b2_snapshot_fixture._response(
                        b2_snapshot_fixture._unavailable_frame(
                            "owner_filter_mismatch"
                        )
                    )
                rebound = rebind_domain_response(
                    value,
                    binding=self.binding,
                    nonce=nonce,
                    requested_owner=owner_character_id,
                    old_player=b2_snapshot_fixture.PLAYER_CHARACTER_ID,
                    old_owner=b2_snapshot_fixture.OWNER_CHARACTER_ID,
                )
                if self.partial_b2 and owner_character_id == actual_owner:
                    rebound["pip"].pop("case_serial")
                return rebound

            def query_zhongguo_incident_snapshot_v1(
                self,
                nonce: str,
                *,
                expected_revision: int,
                owner_character_id: int,
                profile: str,
            ) -> dict[str, object]:
                assert expected_revision == int(self.binding["revision"])
                self.calls.append(
                    (
                        "incident",
                        int(self.binding["connection_generation"]),
                        profile,
                        owner_character_id,
                    )
                )
                actual_owner = domain_owner_contract[
                    "incident_owner_character_id"
                ]
                if owner_character_id != actual_owner:
                    frame = incident_acl_frame(profile)
                elif profile == "x":
                    frame = incident_snapshot_fixture.na_frame(profile)
                elif profile == "y":
                    frame = incident_snapshot_fixture.incident_frame(
                        profile, "pending"
                    )
                else:
                    frame = incident_snapshot_fixture.incident_frame(
                        profile, "consumed"
                    )
                value = incident_snapshot_fixture.response(frame, profile)
                return rebind_domain_response(
                    value,
                    binding=self.binding,
                    nonce=nonce,
                    requested_owner=owner_character_id,
                    old_player=incident_snapshot_fixture.PLAYER,
                    old_owner=incident_snapshot_fixture.OWNER,
                    profile=profile,
                )

            def query_zhongguo_workforce_collective_snapshot_v1(
                self,
                nonce: str,
                *,
                expected_revision: int,
                owner_character_id: int,
            ) -> dict[str, object]:
                assert expected_revision == int(self.binding["revision"])
                self.calls.append(
                    (
                        "workforce",
                        int(self.binding["connection_generation"]),
                        owner_character_id,
                    )
                )
                actual_owner = domain_owner_contract[
                    "workforce_owner_character_id"
                ]
                if owner_character_id == actual_owner:
                    value = workforce_snapshot_fixture.response(
                        workforce_snapshot_fixture.frame(
                            history_count=(
                                2 if self.partial_workforce else 3
                            )
                        )
                    )
                else:
                    unavailable = workforce_bridge_fixture._frame()
                    unavailable["unavailable_reason"] = (
                        "owner_filter_mismatch"
                    )
                    value = workforce_snapshot_fixture.response(
                        workforce_snapshot_fixture.frame()
                    )
                    for key, item in unavailable.items():
                        value[key] = copy.deepcopy(item)
                return rebind_domain_response(
                    value,
                    binding=self.binding,
                    nonce=nonce,
                    requested_owner=owner_character_id,
                    old_player=workforce_snapshot_fixture.PLAYER,
                    old_owner=workforce_snapshot_fixture.OWNER,
                )

            def query_zhongguo_ai_owned_case_snapshot_v1(
                self,
                owner_character_id: int,
                subject_character_id: int,
                nonce: str,
                *,
                expected_revision: int | None = None,
            ) -> dict[str, object]:
                assert expected_revision == int(self.binding["revision"])
                self.calls.append(
                    (
                        "ai_owned",
                        int(self.binding["connection_generation"]),
                        owner_character_id,
                        subject_character_id,
                    )
                )
                actual_owner = domain_owner_contract[
                    "ai_owned_case_owner_character_id"
                ]
                actual_subject = domain_owner_contract[
                    "ai_owned_case_subject_character_id"
                ]
                if (
                    owner_character_id == actual_owner
                    and subject_character_id == actual_subject
                ):
                    value = ai_owned_snapshot_fixture._response()
                    if self.partial_ai_owned:
                        value["route"].pop("kind")
                else:
                    value = ai_owned_snapshot_fixture._response(
                        ai_owned_snapshot_fixture._unavailable_frame(
                            "owner_filter_mismatch"
                        )
                    )
                return rebind_domain_response(
                    value,
                    binding=self.binding,
                    nonce=nonce,
                    requested_owner=owner_character_id,
                    old_player=ai_owned_snapshot_fixture.PLAYER,
                    old_owner=ai_owned_snapshot_fixture.OWNER,
                    old_subject=ai_owned_snapshot_fixture.SUBJECT,
                    subject_character_id=subject_character_id,
                    retain_unavailable_owner_binding=True,
                )

        assert list(capture.PHASE2_DOMAIN_CELL_REGISTRY) == [
            "b2_pip_snapshot_query_matrix",
            "incident_xyz_snapshot_query_matrix",
            "workforce_collective_and_three_cycle_matrix",
            "ai_owned_case_matrix",
            "manager_governance_gameplay_action_and_postcondition_matrix",
            "scoreboard_named_widget_and_acl_matrix",
        ]
        assert capture._phase2_unimplemented_domain_cells() == [
            "manager_governance_gameplay_action_and_postcondition_matrix",
            "scoreboard_named_widget_and_acl_matrix",
        ]
        assert capture.PHASE2_MISSING_GAMEPLAY_ACTION_CELLS == (
            "manager_governance_gameplay_action_and_postcondition_matrix",
            "scoreboard_named_widget_action_and_postcondition_matrix",
        )
        manager_registration = capture.PHASE2_DOMAIN_CELL_REGISTRY[
            "manager_governance_gameplay_action_and_postcondition_matrix"
        ]
        assert manager_registration["implementation"] == "provider_pending"
        assert manager_registration["handler_implementation"] == "wired"
        assert manager_registration["readiness"] == "static-ready"
        assert manager_registration["observation_only"] is False
        assert manager_registration["gameplay_action_complete"] is False
        assert manager_registration["required_typed_selector"] == (
            capture.PHASE2_B3_MANAGER_SELECTOR_KIND
        )
        manager_handler_artifacts = temporary_root / "b3-manager-handler"
        manager_handler_artifacts.mkdir()
        manager_handler_service = object()
        with mock.patch.object(
            capture, "run_b3_manager_governance_gameplay_action_cell"
        ) as unbound_action_cell:
            manager_pending = (
                capture.run_phase2_manager_governance_gameplay_action_cell(
                    manager_handler_service,
                    manager_handler_artifacts,
                )
            )
        unbound_action_cell.assert_not_called()
        assert manager_pending["result"] == "RED"
        assert manager_pending["readiness"] == "static-ready"
        assert manager_pending["implementation"] == "provider_pending"
        assert manager_pending["provider_status"] == "provider_pending"
        assert manager_pending["gameplay_action_executed"] is False
        assert manager_pending["gameplay_action_complete"] is False
        assert manager_pending["action_cell_invoked"] is False
        assert manager_pending["action_ack_is_business_postcondition"] is False
        assert manager_pending["provider_observed_postcondition"] is None
        assert manager_pending["missing_requirements"] == [
            {
                "id": "bounded_ai_manager_native_typed_selector",
                "status": "provider_pending",
                "readiness": "static-ready",
                "reason": (
                    "the native typed selector for one bounded AI direct "
                    "manager and its direct subordinate is not yet bound "
                    "to the formal Phase2 runner"
                ),
            }
        ]
        assert json.loads(
            (
                manager_handler_artifacts
                / "07e_phase2_manager_governance_gameplay_action_cell.json"
            ).read_text(encoding="utf-8")
        ) == manager_pending

        typed_manager_selection = {
            "status": "available",
            "selector_kind": capture.PHASE2_B3_MANAGER_SELECTOR_KIND,
            "provider_observed": True,
            "manager_character_id": 8200,
            "subordinate_character_id": 8300,
        }
        manager_cell_green = {
            "schema_version": 1,
            "kind": "zg361_b3_manager_governance_gameplay_action_cell",
            "result": "GREEN",
            "evidence_class": (
                "provider-observed-live-when-run-against-ck3"
            ),
            "fixture_evidence_is_live": False,
            "mcp_only": True,
            "ocr_used": False,
            "coordinates_used": False,
            "test_ui_used": False,
            "action_ack_is_business_postcondition": False,
            "manager_character_id": 8200,
            "subordinate_character_id": 8300,
            "superior_character_id": 8100,
            "source_b1_cycle": 7,
            "transition": {
                "result": "GREEN",
                "gameplay_action_executed": True,
                "gameplay_action_complete": True,
                "background_business_complete": True,
                "action_ack_is_business_postcondition": False,
            },
            "postcondition": {
                "status": "available",
                "readiness": {"ready": True},
            },
            "checks": {
                "provider_status_available": True,
                "provider_readiness_green": True,
            },
        }
        with mock.patch.object(
            capture,
            "run_b3_manager_governance_gameplay_action_cell",
            return_value=copy.deepcopy(manager_cell_green),
        ) as bound_action_cell:
            manager_green = (
                capture.run_phase2_manager_governance_gameplay_action_cell(
                    manager_handler_service,
                    manager_handler_artifacts,
                    typed_selector_provider=lambda service: (
                        copy.deepcopy(typed_manager_selection)
                        if service is manager_handler_service
                        else None
                    ),
                )
            )
        bound_action_cell.assert_called_once_with(
            manager_handler_service,
            manager_character_id=8200,
            subordinate_character_id=8300,
        )
        assert manager_green["result"] == "GREEN"
        assert manager_green["gameplay_action_complete"] is True
        assert manager_green["action_ack_is_business_postcondition"] is False
        assert manager_green["provider_observed_postcondition"] == (
            manager_cell_green["postcondition"]
        )
        assert manager_green["typed_selector"] == typed_manager_selection
        assert manager_green["fixture_evidence_is_live"] is False
        scoreboard_runner_red = {
            "schema_version": 2,
            "cell_id": (
                "scoreboard_named_widget_action_and_postcondition_matrix"
            ),
            "result": "RED",
            "mcp_only": True,
            "surface_matrix": {
                "managed-capable": {"surface_complete": True},
                "received-only": {"surface_complete": True},
            },
            "action_matrix": {
                "managed-capable": [],
                "received-only": [],
            },
            "candidate_batch_complete": True,
            "all_postconditions_verified": True,
            "all_expected_acl_denials_verified": True,
            "per_surface_single_session_binding_verified": True,
            "cross_surface_clean_restart_verified": True,
            "production_capability_advertised": False,
            "promotion_eligible": False,
            "failure_reason": "production_capability_not_advertised",
        }
        scoreboard_runner_artifacts = temporary_root / "scoreboard-runner-red"
        scoreboard_runner_artifacts.mkdir()
        missing_surface_provider = (
            capture.run_phase2_scoreboard_gameplay_action_cell(
                object(), scoreboard_runner_artifacts
            )
        )
        assert missing_surface_provider["result"] == "RED"
        assert missing_surface_provider["promotion_eligible"] is False
        assert missing_surface_provider["failure_reason"] == (
            "scoreboard_surface_preparation_provider_missing"
        )
        assert missing_surface_provider["action_matrix"] == {
            "managed-capable": []
        }
        with mock.patch.object(
            capture,
            "run_zhongguo_scoreboard_action_batch",
            return_value=copy.deepcopy(scoreboard_runner_red),
        ):
            scoreboard_runner_result = (
                capture.run_phase2_scoreboard_gameplay_action_cell(
                    object(), scoreboard_runner_artifacts
                )
            )
        assert scoreboard_runner_result == scoreboard_runner_red
        assert json.loads(
            (
                scoreboard_runner_artifacts
                / "07c_phase2_scoreboard_named_widget_action_cell.json"
            ).read_text(encoding="utf-8")
        ) == scoreboard_runner_red
        forged_scoreboard_green = copy.deepcopy(scoreboard_runner_red)
        forged_scoreboard_green["result"] = "GREEN"
        forged_scoreboard_green["production_capability_advertised"] = True
        with mock.patch.object(
            capture,
            "run_zhongguo_scoreboard_action_batch",
            return_value=forged_scoreboard_green,
        ):
            try:
                capture.run_phase2_scoreboard_gameplay_action_cell(
                    object(), scoreboard_runner_artifacts
                )
            except capture.acceptance.RunnerError as error:
                assert "forged GREEN" in str(error)
            else:
                raise AssertionError(
                    "scoreboard runner accepted GREEN without promotion eligibility"
                )
        for cell_id in (
            "b2_pip_snapshot_query_matrix",
            "incident_xyz_snapshot_query_matrix",
            "workforce_collective_and_three_cycle_matrix",
            "ai_owned_case_matrix",
        ):
            assert capture.PHASE2_DOMAIN_CELL_REGISTRY[cell_id][
                "observation_only"
            ] is True
            assert capture.PHASE2_DOMAIN_CELL_REGISTRY[cell_id][
                "gameplay_action_complete"
            ] is (
                cell_id
                in {
                    "b2_pip_snapshot_query_matrix",
                    "incident_xyz_snapshot_query_matrix",
                    "workforce_collective_and_three_cycle_matrix",
                    "ai_owned_case_matrix",
                }
            )

        domain_service = Phase2DomainService()
        pre_domain_artifacts = temporary_root / "phase2-domain-pre-green"
        pre_domain_artifacts.mkdir()
        pre_domain = capture.run_phase2_domain_query_stage(
            domain_service,
            pre_domain_artifacts,
            stage="pre_restore",
            binding=pre_domain_binding,
            owner_contract=domain_owner_contract,
        )
        assert pre_domain["result"] == "GREEN"
        assert pre_domain["gameplay_green_claimed"] is False
        assert pre_domain["implemented_cells"] == [
            "b2_pip_snapshot_query_matrix",
            "incident_xyz_snapshot_query_matrix",
            "workforce_collective_and_three_cycle_matrix",
            "ai_owned_case_matrix",
        ]
        b2_cell = pre_domain["cells"]["b2_pip_snapshot_query_matrix"]
        assert b2_cell["result"] == "GREEN"
        assert b2_cell["gameplay_action_complete"] is False
        assert b2_cell["typed_unavailable_leaf_count"] > 0
        assert b2_cell["acl_response"]["unavailable_reason"] == (
            "owner_filter_mismatch"
        )
        incident_cell = pre_domain["cells"][
            "incident_xyz_snapshot_query_matrix"
        ]
        assert incident_cell["terminal_kind_counts"] == {
            "na": 1,
            "incident": 2,
        }
        assert incident_cell["typed_unavailable_leaf_count"] > 0
        assert all(
            response["unavailable_reason"] == "owner_filter_mismatch"
            for response in incident_cell["acl_profiles"].values()
        )
        workforce_cell = pre_domain["cells"][
            "workforce_collective_and_three_cycle_matrix"
        ]
        assert workforce_cell["three_cycle_receipt_count"] == 3
        assert workforce_cell["positive_response"]["readiness"][
            "three_cycle_ready"
        ] is True
        assert workforce_cell["acl_response"]["unavailable_reason"] == (
            "owner_filter_mismatch"
        )
        ai_owned_cell = pre_domain["cells"]["ai_owned_case_matrix"]
        assert ai_owned_cell["positive_response"]["route"]["kind"][
            "value"
        ] == capture.ZHONGGUO_AI_OWNED_CASE_BACKGROUND_ROUTE_V1
        assert ai_owned_cell["positive_response"]["route"][
            "visible_event_allowed"
        ]["value"] is False
        assert ai_owned_cell["acl_response"]["unavailable_reason"] == (
            "owner_filter_mismatch"
        )

        domain_service.binding = post_domain_binding
        post_domain_artifacts = temporary_root / "phase2-domain-post-green"
        post_domain_artifacts.mkdir()
        post_domain = capture.run_phase2_domain_query_stage(
            domain_service,
            post_domain_artifacts,
            stage="post_restore",
            binding=post_domain_binding,
            owner_contract=domain_owner_contract,
        )
        consistency_artifacts = temporary_root / "phase2-domain-restore-green"
        consistency_artifacts.mkdir()
        consistency = capture.compare_phase2_domain_query_stages(
            pre_domain, post_domain, consistency_artifacts
        )
        assert consistency["result"] == "GREEN"
        assert consistency["checks"]["domain_payloads_restored"] is True
        assert [call[1] for call in domain_service.calls if call[0] == "b2"] == [
            4,
            4,
            5,
            5,
        ]
        assert [
            call[1]
            for call in domain_service.calls
            if call[0] == "workforce"
        ] == [4, 4, 5, 5]
        assert [
            call[1]
            for call in domain_service.calls
            if call[0] == "ai_owned"
        ] == [4, 4, 5, 5]

        missing_domain_service = Phase2DomainService()
        missing_domain_service.missing_b2_flag = True
        missing_domain_artifacts = temporary_root / "phase2-domain-capability-red"
        missing_domain_artifacts.mkdir()
        try:
            capture.run_phase2_domain_query_stage(
                missing_domain_service,
                missing_domain_artifacts,
                stage="pre_restore",
                binding=pre_domain_binding,
                owner_contract=domain_owner_contract,
            )
        except capture.acceptance.RunnerError as error:
            assert "lacks its runtime capability/query flag" in str(error)
        else:
            raise AssertionError("domain matrix accepted a missing B2 capability")
        missing_domain_gate = json.loads(
            (
                missing_domain_artifacts
                / "05a_phase2_domain_queries_pre_restore.json"
            ).read_text(encoding="utf-8")
        )
        assert missing_domain_gate["result"] == "RED"

        partial_domain_service = Phase2DomainService()
        partial_domain_service.partial_b2 = True
        partial_domain_artifacts = temporary_root / "phase2-domain-partial-red"
        partial_domain_artifacts.mkdir()
        try:
            capture.run_phase2_domain_query_stage(
                partial_domain_service,
                partial_domain_artifacts,
                stage="pre_restore",
                binding=pre_domain_binding,
                owner_contract=domain_owner_contract,
            )
        except capture.acceptance.RunnerError as error:
            assert "partial or malformed tuple" in str(error)
        else:
            raise AssertionError("domain matrix accepted a partial B2 tuple")

        partial_workforce_service = Phase2DomainService()
        partial_workforce_service.partial_workforce = True
        partial_workforce_artifacts = (
            temporary_root / "phase2-domain-workforce-two-cycle-red"
        )
        partial_workforce_artifacts.mkdir()
        try:
            capture.run_phase2_domain_query_stage(
                partial_workforce_service,
                partial_workforce_artifacts,
                stage="pre_restore",
                binding=pre_domain_binding,
                owner_contract=domain_owner_contract,
            )
        except capture.acceptance.RunnerError as error:
            assert "three-cycle proof" in str(error)
        else:
            raise AssertionError(
                "domain matrix accepted an incomplete Workforce history"
            )

        partial_ai_service = Phase2DomainService()
        partial_ai_service.partial_ai_owned = True
        partial_ai_artifacts = temporary_root / "phase2-domain-ai-partial-red"
        partial_ai_artifacts.mkdir()
        try:
            capture.run_phase2_domain_query_stage(
                partial_ai_service,
                partial_ai_artifacts,
                stage="pre_restore",
                binding=pre_domain_binding,
                owner_contract=domain_owner_contract,
            )
        except capture.acceptance.RunnerError as error:
            assert "partial or malformed tuple" in str(error)
        else:
            raise AssertionError(
                "domain matrix accepted a partial AI-owned case tuple"
            )

        drifted_post = copy.deepcopy(post_domain)
        drifted_post["cells"]["b2_pip_snapshot_query_matrix"][
            "semantic_projection"
        ]["positive"]["date_raw"] += 1
        drift_artifacts = temporary_root / "phase2-domain-restore-red"
        drift_artifacts.mkdir()
        try:
            capture.compare_phase2_domain_query_stages(
                pre_domain, drifted_post, drift_artifacts
            )
        except capture.acceptance.RunnerError as error:
            assert "domain_payloads_restored" in str(error)
        else:
            raise AssertionError("domain restore comparison accepted payload drift")

        def phase2_shutdown(pid: int) -> dict[str, object]:
            return {
                "ck3_pid": pid,
                "ok": True,
                "cleanup_proven": True,
                "tree_gone": True,
                "job_active_processes_final": 0,
                "final_ck3_inventory": {"processes": []},
                "watchdog_state_after": "absent",
                "control_files_absent": {
                    "pid": True,
                    "ready": True,
                    "watchdog_error": True,
                    "unsafe": True,
                },
                "contract_errors": [],
            }

        supervisor_pipe = native_config.pipe_name
        two_pid_session_report = {
            "kind": "ck3_native_headless_session",
            "mode": "native-headless",
            "pipe": supervisor_pipe,
            "pid": 5432,
            "exit_reason": "stop",
            "process_exit_code": None,
            "shutdown": phase2_shutdown(5432),
            "restart_count": 1,
            "restart_shutdowns": [phase2_shutdown(4321)],
            "ok": True,
        }
        two_pid_scenario = {"save_restore_lineage": lineage}
        second_pid_capabilities = {
            "diagnostics": {
                "connected": True,
                "bridge_pid": 5432,
                "connection_generation": 5,
            }
        }
        cleanup_artifacts = temporary_root / "phase2-supervisor-cleanup-green"
        cleanup_artifacts.mkdir()
        cleanup_green = capture.prove_phase2_native_session_cleanup(
            copy.deepcopy(two_pid_session_report),
            cleanup_artifacts,
            initial_pid=4321,
            initial_generation=4,
            expected_pipe=supervisor_pipe,
            scenario_evidence=copy.deepcopy(two_pid_scenario),
            final_capabilities=copy.deepcopy(second_pid_capabilities),
            session_error=None,
            supervisor_stopped=True,
        )
        assert cleanup_green["result"] == "GREEN"
        assert cleanup_green["restore_expected"] is True
        assert cleanup_green["checks"]["restore_queue_consumed_once"] is True
        assert cleanup_green["checks"]["old_pid_shutdown_cleanup_proven"] is True
        assert cleanup_green["checks"]["new_pid_shutdown_cleanup_proven"] is True

        single_pid_report = copy.deepcopy(two_pid_session_report)
        single_pid_report.update(
            {
                "pid": 4321,
                "shutdown": phase2_shutdown(4321),
                "restart_count": 0,
                "restart_shutdowns": [],
            }
        )
        single_pid_artifacts = temporary_root / "phase2-prestart-cleanup-green"
        single_pid_artifacts.mkdir()
        single_pid_cleanup = capture.prove_phase2_native_session_cleanup(
            single_pid_report,
            single_pid_artifacts,
            initial_pid=4321,
            initial_generation=4,
            expected_pipe=supervisor_pipe,
            scenario_evidence={},
            final_capabilities={
                "diagnostics": {
                    "connected": True,
                    "bridge_pid": 4321,
                    "connection_generation": 4,
                }
            },
            session_error=None,
            supervisor_stopped=True,
        )
        assert single_pid_cleanup["result"] == "GREEN"
        assert single_pid_cleanup["restore_expected"] is False

        fake_supervisor_artifacts = temporary_root / "phase2-fake-supervisor-green"
        fake_supervisor_artifacts.mkdir()
        fake_supervisor_entered = threading.Event()
        fake_supervisor_scenario = copy.deepcopy(two_pid_scenario)
        fake_supervisor_lineage = fake_supervisor_scenario[
            "save_restore_lineage"
        ]
        fake_supervisor_lineage["first_connection_generation"] = 1
        fake_supervisor_lineage["second_connection_generation"] = 2
        fake_supervisor_lineage["connection_generation_lineage"] = [1, 2]
        fake_supervisor_final_capabilities = {
            "diagnostics": {
                "connected": True,
                "bridge_pid": 5432,
                "connection_generation": 2,
            }
        }

        def fake_native_session(
            _spec: object,
            **kwargs: object,
        ) -> dict[str, object]:
            assert kwargs["native_bridge"] == native_config
            assert kwargs["verify_prepared_profile"] is False
            stop_event = kwargs["stop_event"]
            assert isinstance(stop_event, threading.Event)
            fake_supervisor_entered.set()
            if not stop_event.wait(timeout=2.0):
                raise RuntimeError("fake supervisor did not receive stop event")
            return copy.deepcopy(two_pid_session_report)

        with mock.patch.object(
            capture, "native_session", side_effect=fake_native_session
        ) as native_session_call:
            fake_supervisor = capture.start_phase2_native_session_supervisor(
                SimpleNamespace(), native_config
            )
            if not fake_supervisor_entered.wait(timeout=1.0):
                raise AssertionError("fake phase-two supervisor did not start")
            fake_thread = fake_supervisor["session_thread"]
            assert isinstance(fake_thread, threading.Thread)
            assert fake_thread.daemon is False
            fake_start_binding = capture.wait_for_phase2_native_session_binding(
                Phase2CapabilityService(
                    {
                        "mode": "native-headless",
                        "backend_id": "native-headless",
                        "visual_fallback": False,
                        "diagnostics": {
                            "connected": True,
                            "bridge_pid": 4321,
                            "connection_generation": 1,
                        },
                    }
                ),
                fake_supervisor,
                fake_supervisor_artifacts,
                timeout_s=1.0,
                poll_interval_s=0.0,
            )
            assert fake_start_binding["bridge_pid"] == 4321
            assert fake_start_binding["connection_generation"] == 1

            class Phase2LivenessService:
                def capabilities(self) -> dict[str, object]:
                    return copy.deepcopy(fake_supervisor_final_capabilities)

                def snapshot(self) -> dict[str, object]:
                    return phase2_snapshot(
                        pid=5432, generation=2, revision=20
                    )

            fake_liveness = capture.phase2_native_session_liveness_gate(
                Phase2LivenessService(),
                fake_supervisor,
                fake_supervisor_artifacts,
                scenario_evidence=fake_supervisor_scenario,
            )
            assert fake_liveness["result"] == "GREEN"
            assert fake_liveness["binding"]["bridge_pid"] == 5432
            fake_cleanup = capture.stop_phase2_native_session_supervisor(
                fake_supervisor,
                fake_supervisor_artifacts,
                initial_pid=4321,
                initial_generation=1,
                expected_pipe=supervisor_pipe,
                scenario_evidence=copy.deepcopy(fake_supervisor_scenario),
                final_capabilities=copy.deepcopy(
                    fake_supervisor_final_capabilities
                ),
            )
        assert native_session_call.call_count == 1
        assert fake_thread.is_alive() is False
        assert fake_cleanup["result"] == "GREEN"

        queue_not_consumed_scenario = copy.deepcopy(two_pid_scenario)
        pending_lineage = queue_not_consumed_scenario["save_restore_lineage"]
        pending_lineage["result"] = "RED"
        pending_lineage["restore_result"] = None
        pending_lineage.pop("second_pid", None)
        pending_lineage.pop("second_connection_generation", None)
        supervisor_red_cases = {
            "queue_not_consumed": (
                single_pid_report,
                queue_not_consumed_scenario,
                {
                    "diagnostics": {
                        "connected": True,
                        "bridge_pid": 4321,
                        "connection_generation": 4,
                    }
                },
                "restore_queue_consumed_once",
            ),
            "old_pid_cleanup_failed": (
                {
                    **copy.deepcopy(two_pid_session_report),
                    "restart_shutdowns": [
                        {
                            **phase2_shutdown(4321),
                            "ok": False,
                            "cleanup_proven": False,
                        }
                    ],
                },
                two_pid_scenario,
                second_pid_capabilities,
                "old_pid_shutdown_cleanup_proven",
            ),
            "restart_count_not_one": (
                {
                    **copy.deepcopy(two_pid_session_report),
                    "restart_count": 2,
                    "restart_shutdowns": [
                        phase2_shutdown(4321),
                        phase2_shutdown(4999),
                    ],
                },
                two_pid_scenario,
                second_pid_capabilities,
                "restart_count_exactly_one",
            ),
            "new_pid_binding_mismatch": (
                two_pid_session_report,
                two_pid_scenario,
                {
                    "diagnostics": {
                        "connected": True,
                        "bridge_pid": 9999,
                        "connection_generation": 5,
                    }
                },
                "final_capabilities_pid_matches",
            ),
        }
        for label, (
            session_report,
            scenario_value,
            capabilities_value,
            failed_check,
        ) in supervisor_red_cases.items():
            red_dir = temporary_root / f"phase2-supervisor-red-{label}"
            red_dir.mkdir()
            try:
                capture.prove_phase2_native_session_cleanup(
                    copy.deepcopy(session_report),
                    red_dir,
                    initial_pid=4321,
                    initial_generation=4,
                    expected_pipe=supervisor_pipe,
                    scenario_evidence=copy.deepcopy(scenario_value),
                    final_capabilities=copy.deepcopy(capabilities_value),
                    session_error=None,
                    supervisor_stopped=True,
                )
            except capture.acceptance.RunnerError as error:
                assert "native_session cleanup RED" in str(error)
                assert failed_check in str(error)
            else:
                raise AssertionError(
                    f"phase-two supervisor accepted RED case {label}"
                )
            cleanup_red = json.loads(
                (red_dir / "09_phase2_native_session_cleanup.json").read_text(
                    encoding="utf-8"
                )
            )
            assert cleanup_red["result"] == "RED"
            assert cleanup_red["checks"][failed_check] is False

        workforce_gate_artifacts = temporary_root / (
            "phase2-workforce-m360-runner-ready"
        )
        workforce_gate_artifacts.mkdir()

        class WorkforceGateService:
            def __init__(self) -> None:
                self.calls: list[str] = []

            def capabilities(self) -> dict[str, object]:
                self.calls.append("capabilities")
                return {
                    "bridge_capabilities": [
                        capture.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
                        "game.command.select-event-option-N",
                    ],
                    "action_steps": [
                        "save-checkpoint",
                        "restore-checkpoint",
                    ],
                }

            def snapshot(self) -> dict[str, object]:
                raise AssertionError("Workforce gate mutated through snapshot")

            def save_checkpoint(self, **_kwargs: object) -> dict[str, object]:
                raise AssertionError("Workforce gate created a checkpoint")

            def restore_checkpoint(self, **_kwargs: object) -> dict[str, object]:
                raise AssertionError("Workforce gate restored a checkpoint")

            def select_event_option(
                self, *_args: object, **_kwargs: object
            ) -> dict[str, object]:
                raise AssertionError("Workforce gate selected #360")

            def query_current_event_window_context_v1(
                self, *_args: object, **_kwargs: object
            ) -> dict[str, object]:
                raise AssertionError("Workforce preflight queried an event")

        workforce_gate_service = WorkforceGateService()
        workforce_prior_lineage = {
            "scope": "phase2_one_save_one_restore_two_pid_lineage",
            "pid_lineage": [4321, 5432],
        }
        workforce_preflight = (
            capture.preflight_phase2_workforce_m360_gameplay_action_cell(
                workforce_gate_service,
                workforce_gate_artifacts,
                owner_character_id=9200,
                subject_character_id=9001,
                seed_contract=ready_seed_contract,
                prior_lineage=workforce_prior_lineage,
            )
        )
        assert workforce_gate_service.calls == ["capabilities"]
        workforce_gate = json.loads(
            (
                workforce_gate_artifacts
                / (
                    "07d_phase2_workforce_m360_gameplay_action_"
                    "preflight.json"
                )
            ).read_text(encoding="utf-8")
        )
        assert workforce_gate == workforce_preflight
        assert workforce_gate["result"] == "GREEN"
        assert workforce_gate["stage"] == (
            "static_runner_ready_live_proof_pending"
        )
        assert workforce_gate["gameplay_action_executed"] is False
        assert workforce_gate["live_proof_claimed"] is False
        assert workforce_gate["checkpoint_created_for_workforce"] is False
        assert workforce_gate["helper_invoked"] is False
        assert workforce_gate["expected_event_definition_key"] == (
            "zg361we.360"
        )
        assert workforce_gate["owner_character_id"] == 9200
        assert workforce_gate["subject_character_id"] == 9001
        assert workforce_gate["prior_lineage"] == workforce_prior_lineage
        assert workforce_gate["missing_requirements"] == []
        assert workforce_gate["requirements"][
            "exact_owner_subject_player_transition"
        ]["result"] == "RUNNER_READY"
        assert workforce_gate["requirements"][
            "same_checkpoint_three_route_restore_lineage"
        ]["independent_route_restores"] == ["A", "B", "C"]
        assert workforce_gate["ocr_used"] is False
        assert workforce_gate["coordinates_used"] is False
        assert workforce_gate["console_used"] is False
        assert workforce_gate["test_decision_used"] is False

        scenario_artifacts = temporary_root / "phase2-independent-scenario-red"
        scenario_artifacts.mkdir()

        class Phase2ManifestService:
            def query_loaded_feature_manifest_v1(
                self, *, expected_revision: int
            ) -> dict[str, object]:
                assert expected_revision == 10
                return phase2_loaded_feature_manifest(scenario_snapshot)

        scenario_snapshot = phase2_snapshot(
            pid=4321, generation=4, revision=10
        )
        missing_domain_seed = copy.deepcopy(ready_seed_contract)
        missing_domain_seed.pop("domain_query_matrix")
        with (
            mock.patch.object(
                capture,
                "wait_for_phase2_paused_snapshot",
                return_value=scenario_snapshot,
            ),
            mock.patch.object(
                capture,
                "run_phase2_save_restore_lineage",
                return_value={"result": "GREEN", "pid_lineage": [4321, 5432]},
            ),
            mock.patch.object(capture, "run_scenario") as legacy_scenario,
            mock.patch.object(capture, "initialize_fixture") as legacy_fixture,
            mock.patch.object(
                capture.acceptance, "wait_for_ocr_text"
            ) as legacy_ocr,
            mock.patch.object(
                capture.acceptance, "navigate_lobby"
            ) as legacy_navigation,
            mock.patch.object(
                capture.acceptance, "ensure_game_paused"
            ) as legacy_pause,
            mock.patch.object(
                capture, "force_ck3_english_keyboard_layout"
            ) as legacy_keyboard,
            mock.patch.object(
                capture.acceptance.ImageGrab, "grab"
            ) as legacy_image,
            mock.patch.object(
                capture.acceptance.pyautogui, "click"
            ) as legacy_coordinate,
        ):
            try:
                capture.run_phase2_live_scenario(
                    Phase2ManifestService(),
                    scenario_artifacts,
                    tracked_ck3_pid=4321,
                    seed_contract=missing_domain_seed,
                )
            except capture.acceptance.RunnerError as error:
                assert "domain matrix RED" in str(error)
            else:
                raise AssertionError(
                    "incomplete independent phase-two scenario claimed GREEN"
                )
        for forbidden_call in (
            legacy_scenario,
            legacy_fixture,
            legacy_ocr,
            legacy_navigation,
            legacy_pause,
            legacy_keyboard,
            legacy_image,
            legacy_coordinate,
        ):
            assert forbidden_call.called is False
        scenario_red = json.loads(
            (scenario_artifacts / "05_phase2_live_scenario.json").read_text(
                encoding="utf-8"
            )
        )
        assert scenario_red["result"] == "RED"
        assert scenario_red["phase2_acceptance_complete"] is False
        assert scenario_red["gameplay_green_claimed"] is False
        assert scenario_red["mcp_only"] is True
        assert scenario_red["legacy_run_scenario_used"] is False
        assert scenario_red["test_decision_used"] is False

        wired_scenario_artifacts = (
            temporary_root / "phase2-b2-incident-pre-post-wired-red"
        )
        wired_scenario_artifacts.mkdir()
        wired_seed_contract = copy.deepcopy(ready_seed_contract)
        wired_seed_contract["domain_query_matrix"] = {
            "schema_version": 1,
            **domain_owner_contract,
        }
        wired_service = Phase2DomainService()
        incident_action_evidence = {
            "schema_version": 1,
            "cell_id": (
                "incident_xyz_gameplay_action_and_postcondition_matrix"
            ),
            "result": "GREEN",
            "mcp_only": True,
            "selection_submissions": [{"event_instance_id": 501}],
            "terminal_profiles": {
                "x": {"kind": "na"},
                "y": {"kind": "incident"},
                "z": {"kind": "incident"},
            },
        }
        b2_action_evidence = {
            "schema_version": 1,
            "cell": "zg361.phase2.b2.pip-response-action",
            "action": "accept",
            "result": "GREEN",
            "mcp_only": True,
            "selection_submission": {
                "accepted": True,
                "status": "submitted",
                "event_instance_id": 601,
                "option_number": 1,
            },
            "postcondition": {
                "same_immutable_case": True,
                "expected_state_transition": [1, 2],
            },
            "ack_is_postcondition": False,
            "postcondition_query_green": True,
        }
        ai_owned_action_evidence = {
            "schema_version": 1,
            "kind": "zg361_ai_owned_case_background_action",
            "result": "GREEN",
            "mcp_only": True,
            "ocr_used": False,
            "coordinates_used": False,
            "test_ui_used": False,
            "gameplay_action_executed": True,
            "gameplay_action_complete": True,
            "background_business_complete": True,
            "action_ack_is_business_postcondition": False,
            "timeline_actions": [
                {
                    "ordinal": 1,
                    "step": "life-advance",
                    "acknowledgement": {
                        "accepted": False,
                        "status": "ack_not_authoritative",
                    },
                    "business_postcondition": True,
                }
            ],
            "provider_observations": [
                {
                    "phase": "pre",
                    "classification": "pending",
                    "reason": "case_not_found",
                },
                {
                    "phase": "after_1",
                    "classification": "postcondition",
                    "reason": None,
                    "receipt_signature": [9400, 9500, 8, 904, 39, 1],
                },
            ],
            "current_event_observation": None,
            "terminal_condition": "new_allowlisted_roster_lock_receipt",
            "failure_reason": None,
        }
        checkpointed_batch_evidence = {
            "schema_version": 1,
            "result": "GREEN",
            "scope": "phase2_checkpointed_gameplay_action_batch",
            "mcp_only": True,
            "timeline_advance_expected": True,
            "b2_pip_gameplay_action_cell": b2_action_evidence,
            "ai_owned_case_gameplay_action_cell": ai_owned_action_evidence,
        }

        def fake_incident_action(
            _service: object,
            *,
            owner_character_id: int,
        ) -> dict[str, object]:
            assert _service is wired_service
            assert owner_character_id == domain_owner_contract[
                "incident_owner_character_id"
            ]
            wired_service.calls.append(("incident-action", 4))
            return copy.deepcopy(incident_action_evidence)

        def fake_b2_action(
            _service: object,
            *,
            owner_character_id: int,
            action: str,
        ) -> dict[str, object]:
            assert _service is wired_service
            assert owner_character_id == domain_owner_contract[
                "b2_pip_owner_character_id"
            ]
            assert action == "accept"
            wired_service.calls.append(("b2-action", 4))
            return copy.deepcopy(b2_action_evidence)

        def fake_ai_owned_action(
            _service: object,
            *,
            owner_character_id: int,
            subject_character_id: int,
            require_transition: bool,
        ) -> dict[str, object]:
            assert _service is wired_service
            assert owner_character_id == domain_owner_contract[
                "ai_owned_case_owner_character_id"
            ]
            assert subject_character_id == domain_owner_contract[
                "ai_owned_case_subject_character_id"
            ]
            assert require_transition is True
            wired_service.calls.append(("ai-owned-action", 4))
            return copy.deepcopy(ai_owned_action_evidence)

        def fake_domain_lineage(
            _service: object,
            _artifacts: Path,
            *,
            tracked_ck3_pid: int,
            checkpointed_gameplay_action: object,
        ) -> dict[str, object]:
            assert _service is wired_service
            assert _artifacts == wired_scenario_artifacts
            assert tracked_ck3_pid == 4321
            assert callable(checkpointed_gameplay_action)
            wired_service.calls.append(("lineage-save", 4))
            action_evidence = checkpointed_gameplay_action()
            assert action_evidence == checkpointed_batch_evidence
            wired_service.calls.append(("lineage-restore", 4, 5))
            wired_service.binding = post_domain_binding
            return {
                "result": "GREEN",
                "scope": "phase2_one_save_one_restore_two_pid_lineage",
                "checkpointed_gameplay_action": copy.deepcopy(
                    action_evidence
                ),
                "after_restore": copy.deepcopy(post_domain_binding),
                "pid_lineage": [4321, 5432],
                "connection_generation_lineage": [4, 5],
            }

        with (
            mock.patch.object(
                capture,
                "wait_for_phase2_paused_snapshot",
                return_value=pre_domain_snapshot,
            ),
            mock.patch.object(
                capture,
                "wait_for_phase2_b2_pip_prompt",
                return_value=pre_domain_snapshot,
            ),
            mock.patch.object(
                capture,
                "run_phase2_save_restore_lineage",
                side_effect=fake_domain_lineage,
            ),
            mock.patch.object(
                capture,
                "run_incident_xyz_gameplay_action_cell",
                side_effect=fake_incident_action,
            ),
            mock.patch.object(
                capture,
                "run_b2_pip_gameplay_action_cell",
                side_effect=fake_b2_action,
            ),
            mock.patch.object(
                capture,
                "run_zhongguo_ai_owned_case_background_action",
                side_effect=fake_ai_owned_action,
            ),
            mock.patch.object(
                capture,
                "run_phase2_scoreboard_gameplay_action_cell",
                return_value=copy.deepcopy(scoreboard_runner_red),
            ) as scoreboard_action_cell,
        ):
            try:
                capture.run_phase2_live_scenario(
                    wired_service,
                    wired_scenario_artifacts,
                    tracked_ck3_pid=4321,
                    seed_contract=wired_seed_contract,
                )
            except capture.acceptance.RunnerError as error:
                assert "runner preflight GREEN" in str(error)
                assert "isolated userdir/bootstrap" in str(error)
            else:
                raise AssertionError(
                    "Workforce #360 missing runtime context claimed the batch GREEN"
                )
        scoreboard_action_cell.assert_called_once_with(
            wired_service, wired_scenario_artifacts
        )
        wired_scenario = json.loads(
            (
                wired_scenario_artifacts / "05_phase2_live_scenario.json"
            ).read_text(encoding="utf-8")
        )
        assert wired_scenario["result"] == "RED"
        assert wired_scenario["gameplay_green_claimed"] is False
        assert wired_scenario["gameplay_acceptance_executed"] is True
        assert wired_scenario["incident_gameplay_action_cell"] == (
            incident_action_evidence
        )
        assert wired_scenario["b2_pip_gameplay_action_cell"] == (
            b2_action_evidence
        )
        assert wired_scenario["ai_owned_case_gameplay_action_cell"] == (
            ai_owned_action_evidence
        )
        manager_scenario_gate = wired_scenario[
            "manager_governance_gameplay_action_cell"
        ]
        assert manager_scenario_gate["result"] == "RED"
        assert manager_scenario_gate["readiness"] == "static-ready"
        assert manager_scenario_gate["implementation"] == "provider_pending"
        assert manager_scenario_gate["provider_status"] == "provider_pending"
        assert manager_scenario_gate["gameplay_action_executed"] is False
        assert manager_scenario_gate[
            "action_ack_is_business_postcondition"
        ] is False
        assert wired_scenario["scoreboard_gameplay_action_cell"] == (
            scoreboard_runner_red
        )
        workforce_scenario_gate = wired_scenario[
            "workforce_collective_gameplay_action_cell"
        ]
        assert workforce_scenario_gate["result"] == "RED"
        assert workforce_scenario_gate["gameplay_action_executed"] is False
        assert workforce_scenario_gate["helper_invoked"] is False
        assert workforce_scenario_gate["owner_character_id"] == (
            domain_owner_contract["workforce_owner_character_id"]
        )
        assert workforce_scenario_gate["subject_character_id"] == (
            post_domain_binding["player_character_id"]
        )
        assert wired_scenario["completed_gameplay_action_cells"] == [
            "incident_xyz_gameplay_action_and_postcondition_matrix",
            "b2_pip_gameplay_action_and_postcondition_matrix",
            "ai_owned_case_gameplay_action_and_postcondition_matrix",
        ]
        assert wired_scenario["completed_observation_only_cells"] == [
            "b2_pip_snapshot_query_matrix",
            "incident_xyz_snapshot_query_matrix",
            "workforce_collective_and_three_cycle_matrix",
            "ai_owned_case_matrix",
        ]
        assert wired_scenario["unimplemented_domain_cells"] == [
            "manager_governance_gameplay_action_and_postcondition_matrix",
            "scoreboard_named_widget_and_acl_matrix",
        ]
        assert wired_scenario["missing_gameplay_action_cells"] == list(
            capture.PHASE2_MISSING_GAMEPLAY_ACTION_CELLS
        )
        assert (
            "incident_xyz_gameplay_action_and_postcondition_matrix"
            not in wired_scenario["missing_gameplay_action_cells"]
        )
        assert (
            "b2_pip_gameplay_action_and_postcondition_matrix"
            not in wired_scenario["missing_gameplay_action_cells"]
        )
        assert (
            "ai_owned_case_gameplay_action_and_postcondition_matrix"
            not in wired_scenario["missing_gameplay_action_cells"]
        )
        preserved_action = json.loads(
            (
                wired_scenario_artifacts
                / "05_phase2_incident_xyz_gameplay_action_cell.json"
            ).read_text(encoding="utf-8")
        )
        assert preserved_action == incident_action_evidence
        preserved_b2_action = json.loads(
            (
                wired_scenario_artifacts
                / "05_phase2_b2_pip_gameplay_action_cell.json"
            ).read_text(encoding="utf-8")
        )
        assert preserved_b2_action == b2_action_evidence
        preserved_ai_owned_action = json.loads(
            (
                wired_scenario_artifacts
                / "05_phase2_ai_owned_case_gameplay_action_cell.json"
            ).read_text(encoding="utf-8")
        )
        assert preserved_ai_owned_action == ai_owned_action_evidence
        preserved_manager_gate = json.loads(
            (
                wired_scenario_artifacts
                / "07e_phase2_manager_governance_gameplay_action_cell.json"
            ).read_text(encoding="utf-8")
        )
        assert preserved_manager_gate == manager_scenario_gate
        preserved_workforce_gate = json.loads(
            (
                wired_scenario_artifacts
                / "08_phase2_workforce_m360_gameplay_action_cell.json"
            ).read_text(encoding="utf-8")
        )
        assert preserved_workforce_gate == workforce_scenario_gate
        assert wired_scenario["pre_restore_domain_queries"]["result"] == (
            "GREEN"
        )
        assert wired_scenario["save_restore_lineage"]["result"] == "GREEN"
        assert wired_scenario["post_restore_domain_queries"]["result"] == (
            "GREEN"
        )
        assert wired_scenario["domain_restore_consistency"]["result"] == (
            "GREEN"
        )
        first_pre_query = next(
            index
            for index, call in enumerate(wired_service.calls)
            if call[0] == "b2" and call[1] == 4
        )
        lineage_save_call = wired_service.calls.index(("lineage-save", 4))
        b2_action_call = wired_service.calls.index(("b2-action", 4))
        ai_owned_action_call = wired_service.calls.index(
            ("ai-owned-action", 4)
        )
        lineage_restore_call = wired_service.calls.index(
            ("lineage-restore", 4, 5)
        )
        first_post_query = next(
            index
            for index, call in enumerate(wired_service.calls)
            if call[0] == "b2" and call[1] == 5
        )
        action_call = wired_service.calls.index(("incident-action", 4))
        assert (
            action_call
            < first_pre_query
            < lineage_save_call
            < b2_action_call
            < ai_owned_action_call
            < lineage_restore_call
            < first_post_query
        )

        incident_red_artifacts = temporary_root / "phase2-incident-action-red"
        incident_red_artifacts.mkdir()
        incident_red_evidence = {
            "schema_version": 1,
            "cell_id": (
                "incident_xyz_gameplay_action_and_postcondition_matrix"
            ),
            "result": "RED",
            "selection_submissions": [{"event_instance_id": 777}],
            "failure_reason": "fixture terminal mismatch",
        }
        with mock.patch.object(
            capture,
            "run_incident_xyz_gameplay_action_cell",
            side_effect=capture.IncidentActionCellError(
                "fixture terminal mismatch", incident_red_evidence
            ),
        ):
            try:
                capture.run_phase2_incident_gameplay_action_cell(
                    wired_service,
                    incident_red_artifacts,
                    owner_character_id=domain_owner_contract[
                        "incident_owner_character_id"
                    ],
                )
            except capture.acceptance.RunnerError as error:
                assert "fixture terminal mismatch" in str(error)
            else:
                raise AssertionError("Incident RED evidence was accepted")
        assert json.loads(
            (
                incident_red_artifacts
                / "05_phase2_incident_xyz_gameplay_action_cell.json"
            ).read_text(encoding="utf-8")
        ) == incident_red_evidence

        b2_red_artifacts = temporary_root / "phase2-b2-action-red"
        b2_red_artifacts.mkdir()
        b2_red_evidence = {
            "schema_version": 1,
            "cell": "zg361.phase2.b2.pip-response-action",
            "action": "accept",
            "result": "RED",
            "selection_submission": {
                "accepted": True,
                "status": "submitted",
                "event_instance_id": 888,
                "option_number": 1,
            },
            "postcondition_query_green": False,
            "failure_reason": "fixture B2 postcondition mismatch",
        }
        with mock.patch.object(
            capture,
            "run_b2_pip_gameplay_action_cell",
            side_effect=capture.B2PipActionCellError(
                "fixture B2 postcondition mismatch", b2_red_evidence
            ),
        ):
            try:
                capture.run_phase2_b2_pip_gameplay_action_cell(
                    wired_service,
                    b2_red_artifacts,
                    owner_character_id=domain_owner_contract[
                        "b2_pip_owner_character_id"
                    ],
                )
            except capture.acceptance.RunnerError as error:
                assert "fixture B2 postcondition mismatch" in str(error)
            else:
                raise AssertionError("B2 RED evidence was accepted")
        assert json.loads(
            (
                b2_red_artifacts
                / "05_phase2_b2_pip_gameplay_action_cell.json"
            ).read_text(encoding="utf-8")
        ) == b2_red_evidence

        ai_owned_red_artifacts = temporary_root / "phase2-ai-owned-action-red"
        ai_owned_red_artifacts.mkdir()
        ai_owned_red_evidence = {
            "schema_version": 1,
            "kind": "zg361_ai_owned_case_background_action",
            "result": "RED",
            "mcp_only": True,
            "ocr_used": False,
            "coordinates_used": False,
            "test_ui_used": False,
            "gameplay_action_executed": True,
            "gameplay_action_complete": False,
            "background_business_complete": False,
            "action_ack_is_business_postcondition": False,
            "timeline_actions": [
                {
                    "ordinal": 1,
                    "step": "life-advance",
                    "acknowledgement": {
                        "accepted": True,
                        "status": "submitted",
                    },
                    "business_postcondition": False,
                }
            ],
            "provider_observations": [
                {"phase": "pre", "classification": "pending"}
            ],
            "current_event_observation": {
                "status": "available",
                "event_definition_key": "unrelated.player.event.1",
                "response": {
                    "status": "available",
                    "event_definition_key": "unrelated.player.event.1",
                },
            },
            "terminal_condition": "player_visible_event_interrupted",
            "failure_reason": (
                "a player-visible event interrupted the hidden AI-owned path; "
                "no event option was selected"
            ),
        }
        with mock.patch.object(
            capture,
            "run_zhongguo_ai_owned_case_background_action",
            return_value=copy.deepcopy(ai_owned_red_evidence),
        ) as ai_owned_red_helper:
            try:
                capture.run_phase2_ai_owned_case_gameplay_action_cell(
                    wired_service,
                    ai_owned_red_artifacts,
                    owner_character_id=domain_owner_contract[
                        "ai_owned_case_owner_character_id"
                    ],
                    subject_character_id=domain_owner_contract[
                        "ai_owned_case_subject_character_id"
                    ],
                )
            except capture.acceptance.RunnerError as error:
                assert "player_visible_event_interrupted" in str(error)
                assert "result_green" in str(error)
            else:
                raise AssertionError("AI-owned current-event RED was accepted")
        assert ai_owned_red_helper.call_count == 1
        assert json.loads(
            (
                ai_owned_red_artifacts
                / "05_phase2_ai_owned_case_gameplay_action_cell.json"
            ).read_text(encoding="utf-8")
        ) == ai_owned_red_evidence

        class MissingLoaderSnapshotService(LoaderReadinessService):
            def snapshot(self) -> dict[str, object]:
                raise RuntimeError("semantic frontend snapshot unavailable")

        missing_artifacts = temporary_root / "loader-readiness-missing"
        missing_artifacts.mkdir()
        try:
            capture.native_loader_smoke_readiness(
                MissingLoaderSnapshotService(),
                missing_artifacts,
                tracked_ck3_pid=4321,
                timeout_s=0.001,
                stable_observations=2,
                poll_interval_s=0.0,
            )
        except capture.acceptance.RunnerError as error:
            assert "semantic frontend snapshot unavailable" in str(error)
        else:
            raise AssertionError(
                "loader readiness accepted a missing semantic snapshot"
            )
        missing_gate = json.loads(
            (
                missing_artifacts / "01_loader_native_readiness.json"
            ).read_text(encoding="utf-8")
        )
        assert missing_gate["result"] == "RED"
        assert missing_gate["ocr_used"] is False
        assert missing_gate["gameplay_green_claimed"] is False

        benign_userdir = temporary_root / "benign-loader-profile"
        (benign_userdir / "logs").mkdir(parents=True)
        benign_bytes = b"[12:00:00][E] unrelated vanilla diagnostic\n"
        (benign_userdir / "logs" / "error.log").write_bytes(benign_bytes)
        benign_artifacts = temporary_root / "benign-loader-artifacts"
        benign_artifacts.mkdir()
        benign_scan = capture.scan_loader_error_log(
            benign_userdir,
            benign_artifacts,
            timeout_s=1.0,
            stable_samples=1,
            poll_interval_s=0.0,
            minimum_quiet_s=0.0,
        )
        assert benign_scan["result"] == "GREEN"
        assert benign_scan["matches"] == []
        assert (
            benign_artifacts / "02_loader_error.log"
        ).read_bytes() == benign_bytes

        diagnostic_userdir = temporary_root / "diagnostic-loader-profile"
        (diagnostic_userdir / "logs").mkdir(parents=True)
        diagnostic_bytes = (
            b"[12:00:00][E] Variable 'zg361_loader_observation' is set "
            b"but is never used\n"
        )
        (diagnostic_userdir / "logs" / "error.log").write_bytes(
            diagnostic_bytes
        )
        diagnostic_artifacts = temporary_root / "diagnostic-loader-artifacts"
        diagnostic_artifacts.mkdir()
        diagnostic_scan = capture.scan_loader_error_log(
            diagnostic_userdir,
            diagnostic_artifacts,
            timeout_s=1.0,
            stable_samples=1,
            poll_interval_s=0.0,
            minimum_quiet_s=0.0,
        )
        assert diagnostic_scan["result"] == "GREEN"
        assert diagnostic_scan["matches"] == []
        assert diagnostic_scan["project_attributed_line_count"] == 1
        assert (
            diagnostic_artifacts / "02_loader_error.log"
        ).read_bytes() == diagnostic_bytes

        r4_parser_bytes = (
            b"[05:56:36][E][jomini_script_system.cpp:303]: Script system error!\n"
            b"  Error: revoke_court_position effect [ Expected opening bracket ]\n"
            b"  Script location: file: common/scripted_effects/"
            b"zg361_workforce_appointment_fact_native_lifecycle_effects.txt "
            b"line: 84\n"
        )
        r4_parser_matches = capture._loader_error_matches(r4_parser_bytes)
        assert [match["category"] for match in r4_parser_matches] == [
            "parser_or_script",
            "parser_or_script",
        ]
        assert all(
            match["project_attributed_context"] is True
            for match in r4_parser_matches
        )

        r8_adjacent_vanilla_bytes = (
            b"[07:22:09][E][jomini_eventmanager.cpp:119]: "
            b"'zga_acceptance.13' does not have a valid namespace\n"
            b"[07:22:09][E][pdx_persistent_reader.cpp:216]: "
            b"Unknown event: zga_acceptance.13\n"
            b"[07:22:12][E][jomini_script_system.cpp:303]: Script system error!\n"
            b"  Error: untyped trigger [ Scoped vanilla character is not valid ]\n"
            b"  Script location: file: gfx/court_scene/scene_cultures/"
            b"00_default_cultures.txt line: 2\n"
        )
        assert capture._loader_error_matches(r8_adjacent_vanilla_bytes) == []

        quiet_artifacts = temporary_root / "quiet-loader-artifacts"
        quiet_artifacts.mkdir()
        quiet_scan = capture.scan_loader_error_log(
            benign_userdir,
            quiet_artifacts,
            timeout_s=1.0,
            stable_samples=1,
            poll_interval_s=0.001,
            minimum_quiet_s=0.01,
        )
        assert quiet_scan["result"] == "GREEN"
        assert quiet_scan["quiet_seconds_observed"] >= 0.01

        broken_userdir = temporary_root / "broken-loader-profile"
        (broken_userdir / "logs").mkdir(parents=True)
        broken_bytes = (
            b"[12:00:00][E] mod/zg361/events/zg361_events.txt\n"
            b"[12:00:00][E] Parse error: unexpected token\n"
        )
        (broken_userdir / "logs" / "error.log").write_bytes(broken_bytes)
        broken_artifacts = temporary_root / "broken-loader-artifacts"
        broken_artifacts.mkdir()
        try:
            capture.scan_loader_error_log(
                broken_userdir,
                broken_artifacts,
                timeout_s=17.0,
                stable_samples=1,
                poll_interval_s=0.0,
            )
        except capture.acceptance.RunnerError as error:
            assert "loader error signature" in str(error)
        else:
            raise AssertionError(
                "loader error scan accepted a ZhongGuo parser failure"
            )
        broken_scan = json.loads(
            (
                broken_artifacts / "02_loader_error_scan.json"
            ).read_text(encoding="utf-8")
        )
        assert broken_scan["result"] == "RED"
        assert broken_scan["counts_by_category"]["parser_or_script"] == 1
        assert broken_scan[
            "loader_error_detected_before_quiet_window"
        ] is True
        assert (
            broken_artifacts / "02_loader_error.log"
        ).read_bytes() == broken_bytes

        loader_helpers = "\n".join(
            (
                inspect.getsource(capture.native_loader_smoke_readiness),
                inspect.getsource(capture.scan_loader_error_log),
            )
        )
        for forbidden in (
            "acceptance.wait_for_ocr_text",
            "acceptance.find_ocr_text",
            "acceptance.ocr_results",
            "acceptance.ImageGrab",
            "acceptance.pyautogui",
            "acceptance.focus_ck3",
            "acceptance.deliberate_click",
            "acceptance.navigate_lobby",
        ):
            assert forbidden not in loader_helpers, forbidden
        assert capture.LOADER_ERROR_LOG_MINIMUM_QUIET_S >= 15.0
        loader_scan_signature = inspect.signature(
            capture.scan_loader_error_log
        )
        assert loader_scan_signature.parameters[
            "minimum_quiet_s"
        ].default == capture.LOADER_ERROR_LOG_MINIMUM_QUIET_S
        assert loader_scan_signature.parameters[
            "timeout_s"
        ].default == capture.LOADER_ERROR_LOG_TIMEOUT_S
        assert capture.LOADER_ERROR_LOG_TIMEOUT_S >= (
            capture.LOADER_ERROR_LOG_MINIMUM_QUIET_S + 15.0
        )
        loader_scan_source = inspect.getsource(
            capture.scan_loader_error_log
        )
        assert "quiet_seconds >= minimum_quiet_s" in loader_scan_source
        assert "if matches:" in loader_scan_source
        assert loader_scan_source.index("if matches:") < (
            loader_scan_source.index(
                "quiet_seconds >= minimum_quiet_s"
            )
        )

        gate_artifacts = temporary_root / "phase2-loader-gate-green"
        gate_artifacts.mkdir()
        gate_userdir = temporary_root / "phase2-loader-gate-profile"
        gate_userdir.mkdir()
        gate_calls: list[str] = []
        green_loader_stage = {
            "result": "GREEN",
            "state": "loader_stage_ready",
            "stage": "load_save",
        }
        green_readiness = {"result": "GREEN", "tracked_ck3_pid": 4321}
        green_error_scan = {"result": "GREEN", "matches": []}
        green_mounts = ["product-mount", "fixture-mount"]

        def green_loader_stage_call(
            *_args: object, **_kwargs: object
        ) -> dict[str, object]:
            expected_args = (
                gate_userdir / "logs",
                gate_artifacts / "01_phase2_loader_stage_progress.jsonl",
            )
            if _args != expected_args:
                raise AssertionError(
                    f"loader-stage paths drifted: {_args!r} != {expected_args!r}"
                )
            if _kwargs != {
                "timeout_seconds": capture.NATIVE_LOADER_READINESS_TIMEOUT_S
            }:
                raise AssertionError(
                    f"loader-stage timing contract drifted: {_kwargs!r}"
                )
            gate_calls.append("loader_stage")
            return green_loader_stage

        def green_readiness_call(
            *_args: object, **_kwargs: object
        ) -> dict[str, object]:
            gate_calls.append("native_readiness")
            return green_readiness

        def green_error_call(
            *_args: object, **_kwargs: object
        ) -> dict[str, object]:
            gate_calls.append("error_log_scan")
            return green_error_scan

        def green_phase2_capability_call(
            *_args: object, **_kwargs: object
        ) -> dict[str, object]:
            gate_calls.append("phase2_capabilities")
            return {"result": "GREEN", "missing_requirements": []}

        def green_mount_call(*_args: object, **_kwargs: object) -> list[str]:
            gate_calls.append("mount_inventory")
            return green_mounts

        with (
            mock.patch.object(
                capture,
                "wait_for_phase2_seed_loader_stage",
                side_effect=green_loader_stage_call,
            ),
            mock.patch.object(
                capture,
                "native_loader_smoke_readiness",
                side_effect=green_readiness_call,
            ),
            mock.patch.object(
                capture,
                "phase2_runtime_capability_preflight",
                side_effect=green_phase2_capability_call,
            ),
            mock.patch.object(
                capture,
                "scan_loader_error_log",
                side_effect=green_error_call,
            ),
            mock.patch.object(
                capture,
                "verify_runtime_load_order",
                side_effect=green_mount_call,
            ),
        ):
            green_gate = capture.run_loader_gate(
                SimpleNamespace(),
                gate_artifacts,
                gate_userdir,
                {},
                tracked_ck3_pid=4321,
                phase2_live_batch=True,
            )
        if gate_calls != [
            "loader_stage",
            "native_readiness",
            "phase2_capabilities",
            "error_log_scan",
            "mount_inventory",
        ]:
            raise AssertionError(f"loader gate order drifted: {gate_calls!r}")
        if green_gate["result"] != "GREEN":
            raise AssertionError(f"loader gate was not GREEN: {green_gate!r}")
        if green_gate["same_pid_gameplay_continuation_authorized"] is not True:
            raise AssertionError(
                "phase-two loader gate did not authorize continuation"
            )
        if green_gate["append_only_loader_stage"] != green_loader_stage:
            raise AssertionError("GREEN loader-stage evidence was not preserved")
        persisted_green_gate = json.loads(
            (gate_artifacts / "03_loader_gate.json").read_text(encoding="utf-8")
        )
        if persisted_green_gate != green_gate:
            raise AssertionError(
                "persisted GREEN loader gate differs from return value"
            )

        loader_only_artifacts = temporary_root / "loader-smoke-independent-gate"
        loader_only_artifacts.mkdir()
        gate_calls.clear()
        with (
            mock.patch.object(
                capture,
                "wait_for_phase2_seed_loader_stage",
            ) as forbidden_loader_stage,
            mock.patch.object(
                capture,
                "native_loader_smoke_readiness",
                side_effect=green_readiness_call,
            ),
            mock.patch.object(
                capture, "phase2_runtime_capability_preflight"
            ) as forbidden_phase2_capability,
            mock.patch.object(
                capture,
                "scan_loader_error_log",
                side_effect=green_error_call,
            ),
            mock.patch.object(
                capture,
                "verify_runtime_load_order",
                side_effect=green_mount_call,
            ),
        ):
            loader_only_gate = capture.run_loader_gate(
                SimpleNamespace(),
                loader_only_artifacts,
                gate_userdir,
                {},
                tracked_ck3_pid=4321,
                phase2_live_batch=False,
            )
        if gate_calls != [
            "native_readiness",
            "error_log_scan",
            "mount_inventory",
        ]:
            raise AssertionError(
                f"loader-smoke-only gate order drifted: {gate_calls!r}"
            )
        if forbidden_loader_stage.called:
            raise AssertionError("loader-smoke-only invoked the phase-two stage")
        if forbidden_phase2_capability.called:
            raise AssertionError("loader-smoke-only invoked phase-two preflight")
        if loader_only_gate["result"] != "GREEN":
            raise AssertionError("loader-smoke-only gate was not GREEN")
        if loader_only_gate["phase2_capability_preflight"] is not None:
            raise AssertionError("loader-smoke-only persisted phase-two preflight")
        if loader_only_gate["append_only_loader_stage"] is not None:
            raise AssertionError("loader-smoke-only persisted phase-two loader stage")
        if (
            loader_only_gate["same_pid_gameplay_continuation_authorized"]
            is not False
        ):
            raise AssertionError("loader-smoke-only authorized gameplay continuation")

        red_loader_stage_artifacts = (
            temporary_root / "phase2-loader-stage-parser-red"
        )
        red_loader_stage_artifacts.mkdir()
        parser_red_evidence = {
            "result": "RED",
            "state": "loader_parse_red",
            "stage": "database_init",
            "fatal_error_count": 4,
        }
        with (
            mock.patch.object(
                capture,
                "wait_for_phase2_seed_loader_stage",
                side_effect=capture.LoaderStageError(
                    "known product parser errors stalled database init",
                    parser_red_evidence,
                ),
            ),
            mock.patch.object(
                capture, "native_loader_smoke_readiness"
            ) as red_stage_readiness,
            mock.patch.object(
                capture, "phase2_runtime_capability_preflight"
            ) as red_stage_capability,
            mock.patch.object(
                capture, "scan_loader_error_log"
            ) as red_stage_scan,
            mock.patch.object(
                capture, "verify_runtime_load_order"
            ) as red_stage_mount,
        ):
            try:
                capture.run_loader_gate(
                    SimpleNamespace(),
                    red_loader_stage_artifacts,
                    gate_userdir,
                    {},
                    tracked_ck3_pid=4321,
                    phase2_live_batch=True,
                )
            except capture.acceptance.RunnerError as error:
                if "loader_parse_red" not in str(error):
                    raise
            else:
                raise AssertionError("loader gate accepted parser-stage RED")
        if any(
            call.called
            for call in (
                red_stage_readiness,
                red_stage_capability,
                red_stage_scan,
                red_stage_mount,
            )
        ):
            raise AssertionError("parser-stage RED did not stop all later gates")
        persisted_parser_red = json.loads(
            (red_loader_stage_artifacts / "03_loader_gate.json").read_text(
                encoding="utf-8"
            )
        )
        if (
            persisted_parser_red["append_only_loader_stage"]
            != parser_red_evidence
        ):
            raise AssertionError("typed parser-stage evidence was not preserved")

        red_readiness_artifacts = (
            temporary_root / "phase2-loader-gate-readiness-red"
        )
        red_readiness_artifacts.mkdir()
        with (
            mock.patch.object(
                capture,
                "wait_for_phase2_seed_loader_stage",
                return_value=green_loader_stage,
            ),
            mock.patch.object(
                capture,
                "native_loader_smoke_readiness",
                return_value={"result": "RED"},
            ),
            mock.patch.object(
                capture, "phase2_runtime_capability_preflight"
            ) as red_capability,
            mock.patch.object(capture, "scan_loader_error_log") as red_scan,
            mock.patch.object(capture, "verify_runtime_load_order") as red_mount,
        ):
            try:
                capture.run_loader_gate(
                    SimpleNamespace(),
                    red_readiness_artifacts,
                    gate_userdir,
                    {},
                    tracked_ck3_pid=4321,
                    phase2_live_batch=True,
                )
            except capture.acceptance.RunnerError as error:
                if "native loader readiness" not in str(error):
                    raise
            else:
                raise AssertionError("loader gate accepted RED native readiness")
            if red_capability.called or red_scan.called or red_mount.called:
                raise AssertionError(
                    "loader gate did not fail fast after readiness RED"
                )

        red_capability_artifacts = (
            temporary_root / "phase2-loader-gate-capability-red"
        )
        red_capability_artifacts.mkdir()
        with (
            mock.patch.object(
                capture,
                "wait_for_phase2_seed_loader_stage",
                return_value=green_loader_stage,
            ),
            mock.patch.object(
                capture,
                "native_loader_smoke_readiness",
                return_value=green_readiness,
            ),
            mock.patch.object(
                capture,
                "phase2_runtime_capability_preflight",
                side_effect=capture.acceptance.RunnerError(
                    "MCP capability RED: workforce_collective_snapshot"
                ),
            ),
            mock.patch.object(capture, "scan_loader_error_log") as red_scan,
            mock.patch.object(capture, "verify_runtime_load_order") as red_mount,
        ):
            try:
                capture.run_loader_gate(
                    SimpleNamespace(),
                    red_capability_artifacts,
                    gate_userdir,
                    {},
                    tracked_ck3_pid=4321,
                    phase2_live_batch=True,
                )
            except capture.acceptance.RunnerError as error:
                assert "MCP capability RED" in str(error)
            else:
                raise AssertionError("loader gate accepted capability RED")
            if red_scan.called or red_mount.called:
                raise AssertionError(
                    "loader gate did not fail before log/mount after capability RED"
                )

        red_scan_artifacts = temporary_root / "phase2-loader-gate-scan-red"
        red_scan_artifacts.mkdir()
        with (
            mock.patch.object(
                capture,
                "wait_for_phase2_seed_loader_stage",
                return_value=green_loader_stage,
            ),
            mock.patch.object(
                capture,
                "native_loader_smoke_readiness",
                return_value=green_readiness,
            ),
            mock.patch.object(
                capture,
                "phase2_runtime_capability_preflight",
                return_value={"result": "GREEN"},
            ),
            mock.patch.object(
                capture,
                "scan_loader_error_log",
                return_value={"result": "RED"},
            ),
            mock.patch.object(capture, "verify_runtime_load_order") as red_mount,
        ):
            try:
                capture.run_loader_gate(
                    SimpleNamespace(),
                    red_scan_artifacts,
                    gate_userdir,
                    {},
                    tracked_ck3_pid=4321,
                    phase2_live_batch=True,
                )
            except capture.acceptance.RunnerError as error:
                if "error.log scan" not in str(error):
                    raise
            else:
                raise AssertionError("loader gate accepted RED error.log scan")
            if red_mount.called:
                raise AssertionError("loader gate did not fail fast after scan RED")

        red_mount_artifacts = temporary_root / "phase2-loader-gate-mount-red"
        red_mount_artifacts.mkdir()
        with (
            mock.patch.object(
                capture,
                "wait_for_phase2_seed_loader_stage",
                return_value=green_loader_stage,
            ),
            mock.patch.object(
                capture,
                "native_loader_smoke_readiness",
                return_value=green_readiness,
            ),
            mock.patch.object(
                capture,
                "phase2_runtime_capability_preflight",
                return_value={"result": "GREEN"},
            ),
            mock.patch.object(
                capture,
                "scan_loader_error_log",
                return_value=green_error_scan,
            ),
            mock.patch.object(
                capture,
                "verify_runtime_load_order",
                side_effect=capture.acceptance.RunnerError("mount inventory RED"),
            ),
        ):
            try:
                capture.run_loader_gate(
                    SimpleNamespace(),
                    red_mount_artifacts,
                    gate_userdir,
                    {},
                    tracked_ck3_pid=4321,
                    phase2_live_batch=True,
                )
            except capture.acceptance.RunnerError as error:
                if "mount inventory RED" not in str(error):
                    raise
            else:
                raise AssertionError("loader gate accepted RED mount inventory")
        persisted_red_mount = json.loads(
            (red_mount_artifacts / "03_loader_gate.json").read_text(
                encoding="utf-8"
            )
        )
        if persisted_red_mount["result"] != "RED":
            raise AssertionError("mount failure was not persisted as RED")
        if persisted_red_mount[
            "same_pid_gameplay_continuation_authorized"
        ] is not False:
            raise AssertionError("RED loader gate authorized gameplay continuation")

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
            main_result = capture.main(
                artifacts_dir=str(launch_artifacts),
                keep_userdir=True,
                bridge_dll=str(dll),
                bridge_injector=str(injector),
                bridge_pipe=explicit_pipe,
            )
            assert main_result == 0
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

        loader_launch_artifacts = temporary_root / "loader-launch-wiring"
        with (
            mock.patch.object(
                capture, "preflight", return_value=runtime_identity
            ) as loader_preflight,
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
            mock.patch.object(
                capture.isolated, "verify_protected_storage"
            ),
            mock.patch.object(capture, "write_evidence_index"),
            mock.patch.object(
                capture,
                "run_cell",
                return_value={"result": "GREEN", "error_reason": None},
            ) as loader_run_cell,
        ):
            loader_main_result = capture.main(
                artifacts_dir=str(loader_launch_artifacts),
                keep_userdir=True,
                loader_smoke=True,
                bridge_dll=str(dll),
                bridge_injector=str(injector),
                bridge_pipe=explicit_pipe,
            )
            assert loader_main_result == 0
        assert loader_preflight.call_args.kwargs[
            "require_visual_tools"
        ] is False
        assert loader_run_cell.call_args.kwargs["loader_smoke"] is True
        assert loader_run_cell.call_args.kwargs["promo_capture"] is False
        assert loader_run_cell.call_args.kwargs[
            "promo_camera_probe"
        ] is False
        loader_matrix = json.loads(
            (loader_launch_artifacts / "report.json").read_text(
                encoding="utf-8"
            )
        )
        assert loader_matrix["loader_smoke_only"] is True
        assert loader_matrix["gameplay_acceptance_executed"] is False
        assert loader_matrix["gameplay_green_claimed"] is False

        phase2_launch_artifacts = temporary_root / "phase2-live-batch-launch-wiring"
        phase2_cell_report = {
            "result": "RED",
            "error_reason": "MCP capability RED: workforce collective missing",
            "gameplay_acceptance_executed": False,
            "gameplay_green_claimed": False,
            "scenario_evidence": {
                "phase2_acceptance_complete": False,
            },
        }
        with (
            mock.patch.object(
                capture, "preflight", return_value=runtime_identity
            ) as phase2_preflight,
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
            mock.patch.object(
                capture.isolated, "verify_protected_storage"
            ),
            mock.patch.object(capture, "write_evidence_index"),
            mock.patch.object(
                capture,
                "run_cell",
                return_value=phase2_cell_report,
            ) as phase2_run_cell,
        ):
            phase2_main_result = capture.main(
                artifacts_dir=str(phase2_launch_artifacts),
                keep_userdir=True,
                phase2_live_batch=True,
                bridge_dll=str(dll),
                bridge_injector=str(injector),
                bridge_pipe=explicit_pipe,
            )
            assert phase2_main_result == 1
        assert phase2_preflight.call_args.kwargs[
            "require_visual_tools"
        ] is True
        assert phase2_run_cell.call_args.kwargs["phase2_live_batch"] is True
        assert phase2_run_cell.call_args.kwargs["loader_smoke"] is False
        assert phase2_run_cell.call_args.kwargs["promo_capture"] is False
        assert phase2_run_cell.call_args.kwargs[
            "promo_camera_probe"
        ] is False
        phase2_matrix = json.loads(
            (phase2_launch_artifacts / "report.json").read_text(
                encoding="utf-8"
            )
        )
        assert phase2_matrix["loader_smoke_only"] is False
        assert phase2_matrix["phase2_live_batch"] is True
        assert phase2_matrix["loader_gate_executed"] is True
        assert phase2_matrix["result"] == "RED"
        assert phase2_matrix["gameplay_acceptance_executed"] is False
        assert phase2_matrix["gameplay_green_claimed"] is False

        false_green_artifacts = temporary_root / "phase2-false-green-rejected"
        false_green_report = {
            "result": "GREEN",
            "error_reason": None,
            "gameplay_acceptance_executed": True,
            "gameplay_green_claimed": True,
            "scenario_evidence": {
                "result": "GREEN",
                "phase2_acceptance_complete": False,
                "mcp_only": True,
                "ocr_used": False,
                "image_used": False,
                "coordinates_used": False,
                "test_decision_used": False,
                "legacy_run_scenario_used": False,
            },
        }
        with (
            mock.patch.object(
                capture, "preflight", return_value=runtime_identity
            ),
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
            mock.patch.object(
                capture.isolated, "verify_protected_storage"
            ),
            mock.patch.object(capture, "write_evidence_index"),
            mock.patch.object(
                capture, "run_cell", return_value=false_green_report
            ),
        ):
            false_green_result = capture.main(
                artifacts_dir=str(false_green_artifacts),
                keep_userdir=True,
                phase2_live_batch=True,
                bridge_dll=str(dll),
                bridge_injector=str(injector),
                bridge_pipe=explicit_pipe,
            )
            if false_green_result != 1:
                raise AssertionError(
                    "phase-two incomplete MCP proof was not downgraded to RED"
                )
        false_green_matrix = json.loads(
            (false_green_artifacts / "report.json").read_text(encoding="utf-8")
        )
        assert false_green_matrix["result"] == "RED"
        assert false_green_matrix["gameplay_green_claimed"] is False
        assert "complete MCP-only scenario proof" in false_green_matrix[
            "error_reason"
        ]

    camera_probe_cell = inspect.getsource(capture.run_cell)
    for token in (
        "elif promo_camera_probe:",
        '"05_title_navigation_probe_preflight"',
        "force_ck3_english_keyboard_layout(artifacts)",
        "run_native_title_navigation_matrix(",
        '"probe_only": True',
        '"ffmpeg_started": False',
        "and not promo_camera_probe",
        "and not loader_smoke",
        "loader_gate_enabled = (",
        "phase2_live_batch or phase2_promo_capture",
        "loader_gate_evidence = run_loader_gate(",
        "elif phase2_live_batch:",
        "run_phase2_live_scenario(",
        '"gameplay_green_claimed": False',
        '"zg361_50_case_cell_executed": False',
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
        '"managed_native_session_supervisor"',
        'else "suspended_inject_resume"',
        "start_phase2_native_session_supervisor(",
        "stop_phase2_native_session_supervisor(",
        "install_phase2_seed(",
        '"phase2_seed_install": phase2_seed_install_evidence',
    ):
        assert token in camera_probe_cell, token
    seed_install_position = camera_probe_cell.index("install_phase2_seed(")
    driver_position = camera_probe_cell.index("NativeHeadlessGameplayDriver(")
    supervisor_position = camera_probe_cell.index(
        "start_phase2_native_session_supervisor("
    )
    assert seed_install_position < driver_position < supervisor_position
    loader_gate_source = inspect.getsource(capture.run_loader_gate)
    for token in (
        "wait_for_phase2_seed_loader_stage(",
        "native_loader_smoke_readiness(",
        "phase2_runtime_capability_preflight(",
        "scan_loader_error_log(userdir, artifacts)",
        "verify_runtime_load_order(userdir, bootstrap)",
        '"03_loader_gate.json"',
        '"same_pid_gameplay_continuation_authorized"',
    ):
        assert token in loader_gate_source, token
    loader_stage_position = loader_gate_source.index(
        "wait_for_phase2_seed_loader_stage("
    )
    loader_readiness_position = loader_gate_source.index(
        "native_loader_smoke_readiness("
    )
    loader_error_position = loader_gate_source.index(
        "scan_loader_error_log(userdir, artifacts)"
    )
    phase2_capability_position = loader_gate_source.index(
        "phase2_runtime_capability_preflight("
    )
    loader_mount_position = loader_gate_source.index(
        "verify_runtime_load_order(userdir, bootstrap)"
    )
    assert loader_stage_position < loader_readiness_position
    assert loader_readiness_position < phase2_capability_position
    assert phase2_capability_position < loader_error_position
    assert loader_error_position < loader_mount_position
    loader_gate_position = camera_probe_cell.index("run_loader_gate(")
    main_menu_position = camera_probe_cell.index("acceptance.wait_for_ocr_text(")
    scenario_position = camera_probe_cell.index("run_scenario(")
    phase2_scenario_position = camera_probe_cell.index(
        "run_phase2_live_scenario("
    )
    cleanup_position = camera_probe_cell.index("stop_tracked(")
    assert loader_gate_position < main_menu_position
    assert loader_gate_position < phase2_scenario_position
    assert main_menu_position < scenario_position
    assert scenario_position < cleanup_position
    assert "stop_tracked(" not in camera_probe_cell[
        loader_gate_position:scenario_position
    ]
    assert camera_probe_cell.count("stop_tracked(") == 1
    preflight_source = inspect.getsource(capture.preflight)
    assert "if require_visual_tools:" in preflight_source
    assert "acceptance._ocr is None" in preflight_source
    assert "acceptance.pyautogui.size()" in preflight_source
    main_source = inspect.getsource(capture.main)
    assert "require_visual_tools = not loader_smoke" in main_source
    assert '"gameplay_acceptance_executed", False' in main_source
    assert "phase2_live_batch=phase2_live_batch" in main_source
    assert "preflight_phase2_seed_contract(" in main_source
    assert "runtime_source=runtime_source" in main_source
    phase2_branch = camera_probe_cell.split(
        "elif phase2_live_batch:", 1
    )[1].split("elif promo_camera_probe:", 1)[0]
    assert "run_phase2_live_scenario(" in phase2_branch
    assert "run_scenario(" not in phase2_branch
    assert "wait_for_ocr_text" not in phase2_branch
    assert "ImageGrab" not in phase2_branch
    assert "initialize_fixture" not in phase2_branch
    runner_source = Path(capture.__file__).read_text(encoding="utf-8")
    assert '"--phase2-live-batch"' in runner_source
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
    try:
        capture.main(
            preflight_only=True,
            promo_camera_probe=True,
            loader_smoke=True,
        )
    except capture.acceptance.RunnerError as error:
        assert "mutually exclusive" in str(error)
    else:
        raise AssertionError("loader smoke accepted a visual promo mode")
    try:
        capture.main(
            preflight_only=True,
            loader_smoke=True,
            phase2_live_batch=True,
        )
    except capture.acceptance.RunnerError as error:
        assert "mutually exclusive" in str(error)
    else:
        raise AssertionError("phase-two batch accepted loader-smoke mode")

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
    assert capture.PHASE2_SEED_PLAYER_HISTORY_ID == "han_6875"
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
    assert capture.PHASE2_PROMO_CAPTURE_MODE == "zhongguo-361-phase2"
    assert capture.PHASE2_PROMO_CAPTURE_CONTRACT_VERSION == 1
    assert capture.PHASE2_PROMO_CAPTURE_PRODUCER_ID == (
        "zhongguo-361-phase2-visual-producer-v1"
    )
    assert capture.PHASE2_PROMO_CLEAN_SPANS == (
        "phase2_fact_quota_calibration",
        "phase2_receipt_appeal_pip",
        "phase2_manager_governance",
        "phase2_promotion_compensation",
        "phase2_hc_workforce",
        "phase2_projects_metrics",
        "phase2_incidents_operations",
        "phase2_cross_cycle_endgame",
    )
    assert not set(capture.PHASE2_PROMO_CLEAN_SPANS).intersection(
        capture.PROMO_CLEAN_SPANS
    )
    assert (
        tuple(item[0] for item in capture.PHASE2_PROMO_CAPTURE_SPAN_MAP)
        == capture.PHASE2_PROMO_CLEAN_SPANS
    )
    recorder_contract = capture.PHASE2_PROMO_CAPTURE_CONTRACT.to_mapping()
    assert recorder_contract["mode"] == capture.PHASE2_PROMO_CAPTURE_MODE
    assert recorder_contract["version"] == 1
    assert recorder_contract["span_ids"] == list(capture.PHASE2_PROMO_CLEAN_SPANS)
    assert len(recorder_contract["span_map"]) == 8
    recorder_source = inspect.getsource(capture.PromoRecorder)
    assert "contract: PromoCaptureContract" in recorder_source
    assert "self.contract.clean_span_ids" in recorder_source
    assert '"capture_contract": self.contract.to_mapping()' in recorder_source
    phase2_capture_source = inspect.getsource(
        capture.run_phase2_promo_capture_scenario
    )
    assert "_require_phase2_promo_capture_producer" in phase2_capture_source
    assert "run_scenario(" not in phase2_capture_source
    assert "run_phase2_live_scenario(" not in phase2_capture_source
    assert '"capture_contract_version"' in phase2_capture_source
    assert "must explicitly return canonical" in phase2_capture_source
    assert "setdefault(" not in phase2_capture_source
    assert '"--phase2-promo-capture"' in runner

    # The runner now installs the concrete managed-runtime adapter when no
    # override is supplied.  Its visual registry remains empty until real
    # feature-specific primitives land, so a live invocation returns typed
    # RED before recorder.start rather than failing on an absent hook.
    prior_default_producer = capture._PHASE2_PROMO_CAPTURE_PRODUCER
    try:
        capture._PHASE2_PROMO_CAPTURE_PRODUCER = None
        built_in = capture._ensure_phase2_promo_capture_producer()
        assert callable(built_in)
        assert built_in is capture._PHASE2_PROMO_CAPTURE_PRODUCER
        assert capture._PHASE2_PROMO_VISUAL_PRIMITIVES == {}
    finally:
        capture._PHASE2_PROMO_CAPTURE_PRODUCER = prior_default_producer

    # A registered producer must carry the complete contract itself.  The
    # acceptance runner may validate the evidence, but it must not fill in
    # omitted metadata (which could hide a producer that never opted into the
    # phase-two contract).  This exercises only the typed hand-off; no CK3,
    # desktop, recorder, or FFmpeg side effect is allowed here.
    with tempfile.TemporaryDirectory() as temporary:
        strict_artifacts = Path(temporary)
        strict_recorder = capture.PromoRecorder(
            strict_artifacts / "promo",
            contract=capture.PHASE2_PROMO_CAPTURE_CONTRACT,
        )
        strict_kwargs = {
            "title_navigation_service": object(),
            "tracked_ck3_pid": 0,
            "native_bridge": object(),
            "preflight_bridge_identity": {},
        }
        prior_producer = capture._PHASE2_PROMO_CAPTURE_PRODUCER

        def invoke_phase2_producer(payload: object) -> object:
            capture.register_phase2_promo_capture_producer(
                lambda *_args, **_kwargs: payload  # type: ignore[return-value]
            )
            try:
                return capture.run_phase2_promo_capture_scenario(
                    object(),
                    strict_artifacts,
                    strict_recorder,
                    **strict_kwargs,
                )
            finally:
                capture._PHASE2_PROMO_CAPTURE_PRODUCER = prior_producer

        expected_contract = capture.PHASE2_PROMO_CAPTURE_CONTRACT.to_mapping()
        canonical_result = {
            "capture_mode": capture.PHASE2_PROMO_CAPTURE_MODE,
            "capture_contract_version": capture.PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
            "capture_contract": copy.deepcopy(expected_contract),
            "producer_evidence": "contract-only",
        }
        accepted_result = invoke_phase2_producer(copy.deepcopy(canonical_result))
        assert accepted_result == canonical_result

        for missing_field in (
            "capture_mode",
            "capture_contract_version",
            "capture_contract",
        ):
            missing_result = copy.deepcopy(canonical_result)
            missing_result.pop(missing_field)
            try:
                invoke_phase2_producer(missing_result)
            except capture.acceptance.RunnerError as error:
                assert isinstance(error, capture.acceptance.RunnerError)
                assert "must explicitly return canonical capture contract fields" in str(
                    error
                )
                assert missing_field in str(error)
            else:
                raise AssertionError(
                    f"producer missing {missing_field} was silently defaulted"
                )

        malformed_results = (
            (
                "result",
                "RED",
                "explicit result that is not GREEN",
            ),
            (
                "result",
                False,
                "explicit result that is not GREEN",
            ),
            (
                "capture_mode",
                "not-zhongguo-361-phase2",
                "non-canonical capture mode",
            ),
            (
                "capture_contract_version",
                2,
                "unsupported capture contract version",
            ),
            (
                "capture_contract",
                {
                    **expected_contract,
                    "unexpected": "must-be-rejected",
                },
                "non-canonical capture contract",
            ),
        )
        for field, value, expected_message in malformed_results:
            malformed = copy.deepcopy(canonical_result)
            malformed[field] = value
            try:
                invoke_phase2_producer(malformed)
            except capture.acceptance.RunnerError as error:
                assert expected_message in str(error)
            else:
                raise AssertionError(
                    f"producer malformed {field} was accepted"
                )

        # Python equality would otherwise let bool/float values masquerade as
        # the canonical string/int contract fields.  The runner must reject
        # those values before any timeline evidence is accepted.
        for invalid_mode in (True, 1):
            malformed = copy.deepcopy(canonical_result)
            malformed["capture_mode"] = invalid_mode
            try:
                invoke_phase2_producer(malformed)
            except capture.acceptance.RunnerError as error:
                assert "non-canonical capture mode" in str(error)
            else:
                raise AssertionError("non-string capture mode was accepted")
        for invalid_version in (True, 1.0):
            malformed = copy.deepcopy(canonical_result)
            malformed["capture_contract_version"] = invalid_version
            try:
                invoke_phase2_producer(malformed)
            except capture.acceptance.RunnerError as error:
                assert "unsupported capture contract version" in str(error)
            else:
                raise AssertionError("non-integer capture version was accepted")
        for invalid_contract_version in (True, 1.0):
            malformed = copy.deepcopy(canonical_result)
            malformed_contract = copy.deepcopy(expected_contract)
            malformed_contract["version"] = invalid_contract_version
            malformed["capture_contract"] = malformed_contract
            try:
                invoke_phase2_producer(malformed)
            except capture.acceptance.RunnerError as error:
                assert "non-canonical capture contract" in str(error)
            else:
                raise AssertionError(
                    "non-canonical nested capture version was accepted"
                )
    assert capture.PROMO_PERSONAL_RESULT_FIELD_REGION == (0.20, 0.34, 0.42, 0.40)

    def fixture_provenance(history_id: str) -> dict[str, object]:
        """Exercise provenance parsing without depending on an installed game tree."""
        with tempfile.TemporaryDirectory() as temporary:
            fixture_root = Path(temporary)
            character_root = (
                fixture_root
                / "Crusader Kings III"
                / "game"
                / "history"
                / "characters"
            )
            title_root = character_root.parent / "titles"
            character_root.mkdir(parents=True)
            title_root.mkdir(parents=True)
            history_ids = (
                capture.real_characters.MANAGER_HISTORY_ID,
                *capture.real_characters.PROMO_REVIEWED_HISTORY_IDS,
            )
            (character_root / "han.txt").write_text(
                "\n".join(f"{value} = {{\n}}" for value in history_ids) + "\n",
                encoding="utf-8",
            )
            title_blocks = [
                "h_china = {\n"
                "\t1063.4.30 = { holder = han_8052 }\n"
                "}"
            ]
            for subject_id, contract in (
                capture.real_characters.REVIEWED_OFFICIAL_CONTRACT.items()
            ):
                title_blocks.append(
                    f"{contract['title_id']} = {{\n"
                    f"\tliege = {contract['liege_title_id']}\n"
                    f"\t{contract['holder_date']} = {{ holder = {subject_id} }}\n"
                    "}"
                )
            (title_root / "e_china.txt").write_text(
                "\n".join(title_blocks) + "\n",
                encoding="utf-8",
            )
            with mock.patch.object(capture, "ROOT", fixture_root):
                return capture.promo_real_character_provenance(history_id)

    provenance = fixture_provenance("han_5253")
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
        candidate_provenance = fixture_provenance(history_id)
        assert [
            row["history_id"] for row in candidate_provenance["subjects"]
        ] == ["han_8052", history_id]
    dynamic_provenance = fixture_provenance("han_6875")
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
            fixture_provenance(rejected_id)
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
    spaceless_latin_cjk_title = [
        {
            "text": "KPI分项证据单",
            "center": [865, 400],
            "bbox": [700, 385, 1030, 417],
        }
    ]
    assert capture.promo_event_title_evidence(
        spaceless_latin_cjk_title, 2560, 1440, "KPI 分项证据单"
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
    elimination_event = [
        {
            "text": "你被列入末位淘汰名单",
            "center": [820, 320],
            "bbox": [575, 301, 1065, 339],
        },
        {
            "text": "要求复核！",
            "center": [930, 740],
            "bbox": [700, 725, 1160, 755],
        },
        {
            "text": "认命致仕，体面退场。",
            "center": [930, 790],
            "bbox": [700, 775, 1160, 805],
        },
        {
            "text": "掀桌起兵！（建立独立派系，对抗主君）",
            "center": [930, 840],
            "bbox": [700, 825, 1160, 855],
        },
    ]
    elimination_title, elimination_option = (
        capture.promo_preferred_product_event_option(
            elimination_event, 2560, 1440
        )
    )
    assert elimination_title == "你被列入末位淘汰名单"
    assert elimination_option is not None
    assert elimination_option["text"].startswith("掀桌起兵")
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
    assert (
        'stop_event_definition_key=f"zg361m.{mechanism_id}"' in policy_body
    )
    assert "native_event_service=timeline_service" in policy_body
    assert 'acceptance.wait_for_ocr_text(\n            event_title,' not in policy_body
    assert 'f"{stem}_preemption_target_event_visible.png"' in policy_body
    assert 'f"{stem}_event.png"' in policy_body
    assert "shutil.copy2(validated_event_artifact, event_artifact)" in policy_body
    assert "acceptance.ensure_game_paused" in policy_body
    assert "open_decision_detail" not in policy_body
    assert "clean_policy_{mechanism_id:03d}_dispatched" in policy_body
    assert "recorder.clean_hold" in policy_body
    assert "clean_policy_chain_completed" in policy_body
    for token in (
        "timeline_service: GameplayBridgeService",
        "speed_one_gate = arm_native_speed_one(",
        'stem=f"{stem}_close"',
        "select_resolved_event_option_native(",
        'expected_option_text=option_text',
        'expected_event_definition_key=f"zg361m.{mechanism_id}"',
        'pause_evidence["native_option_selection"]',
        'expected_predecessor_event_key=f"zg361m.{mechanism_id}"',
        "pause_after_promo_event_click",
        'stem=f"{stem}_close"',
        '"premature_successor_marker_count"',
        'stream.count(successor_marker)',
        'pause_evidence["result"] = "RED"',
        '"policy successor dispatched before predecessor capture"',
    ):
        assert token in policy_body, token
    assert policy_body.index("speed_one_gate = arm_native_speed_one(") < (
        policy_body.index("select_resolved_event_option_native(")
    )
    assert policy_body.index("select_resolved_event_option_native(") < policy_body.index(
        "pause_after_promo_event_click"
    )
    assert "acceptance.wait_for_ocr_text" not in policy_body
    assert "acceptance.deliberate_click" not in policy_body
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
    assert "stop_event_definition_key: str | None = None" in interruption
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
    for token in (
        "pause_bound_native_event_for_definition_query",
        "query_event_definition_identity",
        'status="blocked_event_definition_identity_unavailable"',
        '"identity_method": "event_definition_key"',
        "native_visual_identity_candidate",
        "arm_native_speed_one",
        "pause_after_promo_event_click",
        '"native_mcp_definition_identity_visual_click"',
        '"repeated_visual_option_after_definition_transition"',
    ):
        assert token in interruption, token
    assert interruption.index(
        "pause_bound_native_event_for_definition_query"
    ) < interruption.index("query_event_definition_identity")
    assert "require_settled_revision=True" in interruption
    assert "require_settled_revision=preferred_option_text is not None" not in interruption

    identity_pause = inspect.getsource(
        capture.pause_bound_native_event_for_definition_query
    )
    for token in (
        'service.execute_step(\n                "pause-map", expected_revision=starting_revision',
        'paused.get("paused") is True',
        'observed["active_event_instance_id"] != starting_event',
        'observed["date_raw"] != starting_date',
        'character_id != starting_character_id',
        '"paused_revision": None',
        'f"{stem}_prequery_pause_gate.json"',
    ):
        assert token in identity_pause, token

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

    policy_020_ocr_items = event_frame(
        "第020号普升包与跨部门答辩",
        (
            ("用底账证明真实贡献", (930, 934)),
            ("这季度先不碰，登记制度债", (936, 1043)),
        ),
    )
    assert capture.promo_event_modal_evidence(
        policy_020_ocr_items, 2560, 1440
    )
    assert not capture.promo_event_title_evidence(
        policy_020_ocr_items,
        2560,
        1440,
        "晋升包与跨部门答辩",
    )

    class DefinitionTargetService:
        def __init__(
            self,
            *,
            available: bool,
            paused: bool = True,
            drift_after_pause: str | None = None,
        ) -> None:
            self.available = available
            self.paused = paused
            self.drift_after_pause = drift_after_pause
            self.revision = 40
            self.date_raw = 53146848
            self.event_instance_id = 9
            self.character_id = 77
            self.query_calls: list[tuple[int, int]] = []
            self.pause_calls: list[tuple[str, int | None]] = []

        def snapshot(self) -> dict[str, object]:
            return {
                "revision": self.revision,
                "native_revision": self.revision - 1,
                "date_raw": self.date_raw,
                "paused": self.paused,
                "speed": 1,
                "active_event": {
                    "instance_id": self.event_instance_id,
                    "option_count": 3,
                },
                "played_character": {"character_id": self.character_id},
            }

        def execute_step(
            self, step: str, *, expected_revision: int | None = None
        ) -> dict[str, object]:
            assert step == "pause-map"
            assert expected_revision == self.revision
            self.pause_calls.append((step, expected_revision))
            self.paused = True
            self.revision += 1
            if self.drift_after_pause == "date":
                self.date_raw += 1
            elif self.drift_after_pause == "event":
                self.event_instance_id += 1
            elif self.drift_after_pause == "character":
                self.character_id += 1
            return {"step": step, "accepted": True, "status": "submitted"}

        def query_current_event_window_context_v1(
            self, event_instance_id: int, *, expected_revision: int
        ) -> dict[str, object]:
            self.query_calls.append((event_instance_id, expected_revision))
            if not self.available:
                return {
                    "status": "unavailable",
                    "current_event_window_context": {
                        "event_definition_key": None,
                        "readiness": {
                            "event_definition_identity_ready": False
                        },
                    },
                }
            return {
                "status": "available",
                "current_event_window_context": {
                    "event_definition_key": "zg361m.20",
                    "readiness": {"event_definition_identity_ready": True},
                },
            }

    policy_020_image = FakeDesktopImage(policy_020_ocr_items)
    with tempfile.TemporaryDirectory() as temporary:
        artifacts = Path(temporary)
        target_service = DefinitionTargetService(available=True, paused=False)
        with (
            mock.patch.object(capture.acceptance, "focus_ck3"),
            mock.patch.object(
                capture.acceptance.ImageGrab,
                "grab",
                return_value=policy_020_image,
            ),
            mock.patch.object(
                capture.acceptance,
                "ocr_box_results",
                side_effect=lambda image, _region: [
                    dict(item) for item in image.items
                ],
            ),
            mock.patch.object(
                capture.acceptance,
                "write_recovery_bundle",
                side_effect=write_fake_bundle,
            ),
            mock.patch.object(capture.acceptance, "deliberate_click") as click,
            mock.patch.object(capture.time, "sleep"),
        ):
            target_dismissed = capture.settle_promo_interruptions(
                artifacts,
                "mock_policy_020_ocr_drift",
                observation_s=0.0,
                stop_event_title="晋升包与跨部门答辩",
                stop_event_definition_key="zg361m.20",
                native_event_service=target_service,
            )
        click.assert_not_called()
        assert target_dismissed == []
        assert target_service.pause_calls == [("pause-map", 40)]
        assert target_service.query_calls == [(9, 41)]
        prequery_pause_gate = json.loads(
            (
                artifacts
                / "mock_policy_020_ocr_drift_event_definition_identity_prequery_pause_gate.json"
            ).read_text(encoding="utf-8")
        )
        assert prequery_pause_gate["result"] == "GREEN"
        assert prequery_pause_gate["paused_revision"] == 41
        assert prequery_pause_gate["event_instance_stable"] is True
        assert prequery_pause_gate["date_stable"] is True
        assert prequery_pause_gate["played_character_stable"] is True
        assert (
            artifacts / "mock_policy_020_ocr_drift_target_event_visible.png"
        ).is_file()
        target_gate = json.loads(
            (
                artifacts
                / "mock_policy_020_ocr_drift_target_event_identity_gate.json"
            ).read_text(encoding="utf-8")
        )
        assert target_gate["result"] == "GREEN"
        assert target_gate["visual_title_match"] is False
        assert target_gate["expected_event_definition_key"] == "zg361m.20"
        assert target_gate["observed_event_definition_key"] == "zg361m.20"

    with tempfile.TemporaryDirectory() as temporary:
        artifacts = Path(temporary)
        already_paused_service = DefinitionTargetService(available=True)
        already_paused_gate = (
            capture.pause_bound_native_event_for_definition_query(
                already_paused_service,
                artifacts,
                stem="mock_policy_020_already_paused",
            )
        )
        already_paused_identity = capture.query_event_definition_identity(
            already_paused_service,
            already_paused_gate["snapshot"],
        )
        assert already_paused_service.pause_calls == []
        assert already_paused_service.query_calls == [(9, 40)]
        assert already_paused_identity["event_definition_key"] == "zg361m.20"
        assert already_paused_gate["evidence"]["pause_submission"][
            "status"
        ] == "not_needed_already_paused"

    with tempfile.TemporaryDirectory() as temporary:
        artifacts = Path(temporary)
        unavailable_service = DefinitionTargetService(available=False)
        with (
            mock.patch.object(capture.acceptance, "focus_ck3"),
            mock.patch.object(
                capture.acceptance.ImageGrab,
                "grab",
                return_value=policy_020_image,
            ),
            mock.patch.object(
                capture.acceptance,
                "ocr_box_results",
                side_effect=lambda image, _region: [
                    dict(item) for item in image.items
                ],
            ),
            mock.patch.object(
                capture.acceptance,
                "write_recovery_bundle",
                side_effect=write_fake_bundle,
            ),
            mock.patch.object(capture.acceptance, "deliberate_click") as click,
            mock.patch.object(capture.time, "sleep"),
        ):
            try:
                capture.settle_promo_interruptions(
                    artifacts,
                    "mock_policy_020_identity_unavailable",
                    observation_s=0.0,
                    stop_event_title="晋升包与跨部门答辩",
                    stop_event_definition_key="zg361m.20",
                    native_event_service=unavailable_service,
                )
            except capture.acceptance.RunnerError as exc:
                assert "could not identify the expected promo event" in str(exc)
            else:
                raise AssertionError("unavailable event identity did not fail closed")
        click.assert_not_called()
        assert unavailable_service.pause_calls == []
        assert unavailable_service.query_calls == [(9, 40)]
        unavailable_gate = json.loads(
            (
                artifacts
                / "mock_policy_020_identity_unavailable_event_definition_identity_unavailable_gate.json"
            ).read_text(encoding="utf-8")
        )
        assert unavailable_gate["result"] == "RED"
        unavailable_decision = json.loads(
            (
                artifacts
                / "mock_policy_020_identity_unavailable_event_definition_identity_unavailable_decision.json"
            ).read_text(encoding="utf-8")
        )
        assert unavailable_decision["status"] == (
            "blocked_event_definition_identity_unavailable"
        )

    with tempfile.TemporaryDirectory() as temporary:
        artifacts = Path(temporary)
        drifting_service = DefinitionTargetService(
            available=True,
            paused=False,
            drift_after_pause="date",
        )
        with (
            mock.patch.object(capture.acceptance, "focus_ck3"),
            mock.patch.object(
                capture.acceptance.ImageGrab,
                "grab",
                return_value=policy_020_image,
            ),
            mock.patch.object(
                capture.acceptance,
                "ocr_box_results",
                side_effect=lambda image, _region: [
                    dict(item) for item in image.items
                ],
            ),
            mock.patch.object(
                capture.acceptance,
                "write_recovery_bundle",
                side_effect=write_fake_bundle,
            ),
            mock.patch.object(capture.acceptance, "deliberate_click") as click,
            mock.patch.object(capture.time, "sleep"),
        ):
            try:
                capture.settle_promo_interruptions(
                    artifacts,
                    "mock_policy_020_pause_drift",
                    observation_s=0.0,
                    stop_event_title="晋升包与跨部门答辩",
                    stop_event_definition_key="zg361m.20",
                    native_event_service=drifting_service,
                )
            except capture.acceptance.RunnerError as exc:
                assert "could not identify the expected promo event" in str(exc)
            else:
                raise AssertionError("pause context drift did not fail closed")
        click.assert_not_called()
        assert drifting_service.pause_calls == [("pause-map", 40)]
        assert drifting_service.query_calls == []
        drift_gate = json.loads(
            (
                artifacts
                / "mock_policy_020_pause_drift_event_definition_identity_prequery_pause_gate.json"
            ).read_text(encoding="utf-8")
        )
        assert drift_gate["result"] == "RED"
        assert "date changed" in drift_gate["failure_reason"]

    class NativeVisualDefinitionService:
        def __init__(self) -> None:
            self.revision = 50
            self.speed = 5
            self.paused = False
            self.definition_key = "vanilla.100"
            self.query_calls: list[tuple[int, int, str]] = []
            self.steps: list[str] = []

        def snapshot(self) -> dict[str, object]:
            return {
                "revision": self.revision,
                "native_revision": self.revision,
                "date_raw": 53146848,
                "paused": self.paused,
                "speed": self.speed,
                "active_event": {"instance_id": 9, "option_count": 2},
                "played_character": {"character_id": 77},
            }

        def execute_step(
            self, step: str, *, expected_revision: int | None = None
        ) -> dict[str, object]:
            if step == "pause-map":
                assert expected_revision == self.revision
                self.steps.append(step)
                self.paused = True
                self.revision += 1
                return {"step": step, "accepted": True, "status": "submitted"}
            assert step == "set-speed-1"
            assert expected_revision is None
            self.steps.append(step)
            self.speed = 1
            self.revision += 1
            return {"step": step, "accepted": True, "status": "submitted"}

        def query_current_event_window_context_v1(
            self, event_instance_id: int, *, expected_revision: int
        ) -> dict[str, object]:
            self.query_calls.append(
                (event_instance_id, expected_revision, self.definition_key)
            )
            return {
                "status": "available",
                "current_event_window_context": {
                    "event_definition_key": self.definition_key,
                    "readiness": {"event_definition_identity_ready": True},
                },
            }

        def select_visual_option(self) -> None:
            assert self.definition_key == "vanilla.100"
            self.definition_key = "vanilla.101"
            self.paused = True
            self.revision += 1

    repeated_option = "这季度先不碰，登记制度债"
    predecessor_items = event_frame(
        "例行预算来函",
        ((repeated_option, (936, 1043)),),
    )
    successor_items = event_frame(
        "下一封例行预算来函",
        ((repeated_option, (936, 1043)),),
    )

    class NativeVisualDesktop:
        def __init__(self, service: NativeVisualDefinitionService) -> None:
            self.service = service
            self.successor_frame_returned = False
            self.clicks: list[tuple[int, int]] = []

        def grab(self) -> FakeDesktopImage:
            if self.service.definition_key == "vanilla.100":
                return FakeDesktopImage([dict(item) for item in predecessor_items])
            if not self.successor_frame_returned:
                self.successor_frame_returned = True
                return FakeDesktopImage([dict(item) for item in successor_items])
            return FakeDesktopImage([])

        def click(self, point: tuple[int, int], _label: str) -> None:
            assert point == (936, 1043)
            self.clicks.append(point)
            self.service.select_visual_option()

    with tempfile.TemporaryDirectory() as temporary:
        artifacts = Path(temporary)
        visual_service = NativeVisualDefinitionService()
        visual_desktop = NativeVisualDesktop(visual_service)
        with (
            mock.patch.object(capture.acceptance, "focus_ck3"),
            mock.patch.object(
                capture.acceptance.ImageGrab,
                "grab",
                side_effect=visual_desktop.grab,
            ),
            mock.patch.object(
                capture.acceptance,
                "ocr_box_results",
                side_effect=lambda image, _region: [
                    dict(item) for item in image.items
                ],
            ),
            mock.patch.object(
                capture.acceptance,
                "write_recovery_bundle",
                side_effect=write_fake_bundle,
            ),
            mock.patch.object(
                capture.acceptance,
                "deliberate_click",
                side_effect=visual_desktop.click,
            ),
            mock.patch.object(
                capture.time, "monotonic", side_effect=advancing_clock()
            ),
            mock.patch.object(capture.time, "sleep"),
        ):
            native_visual_dismissed = capture.settle_promo_interruptions(
                artifacts,
                "mock_native_visual_same_option",
                observation_s=0.0,
                stop_event_title="晋升包与跨部门答辩",
                stop_event_definition_key="zg361m.20",
                native_event_service=visual_service,
            )
        assert visual_desktop.clicks == [(936, 1043)]
        assert visual_service.steps == ["pause-map", "set-speed-1"]
        assert len(native_visual_dismissed) == 1
        native_visual_row = native_visual_dismissed[0]
        assert native_visual_row["selection_method"] == (
            "native_mcp_definition_identity_visual_click"
        )
        assert native_visual_row[
            "repeated_visual_option_after_definition_transition"
        ] is True
        native_visual_gate = native_visual_row["native_selection_evidence"]
        assert native_visual_gate["result"] == "GREEN"
        assert native_visual_gate["instance_transition_seen_same_date"] is False
        assert native_visual_gate["definition_transition_seen_same_date"] is True
        assert native_visual_gate["observed_successor_event_key"] == "vanilla.101"
        assert visual_service.query_calls == [
            (9, 51, "vanilla.100"),
            (9, 52, "vanilla.100"),
            (9, 53, "vanilla.101"),
        ]

    class NativeResolvedProductService:
        def __init__(self) -> None:
            self.revision = 60
            self.speed = 5
            self.paused = False
            self.active = True
            self.query_calls: list[tuple[int, int]] = []
            self.steps: list[str] = []
            self.selections: list[tuple[int, int | None, int | None]] = []

        def snapshot(self) -> dict[str, object]:
            return {
                "revision": self.revision,
                "native_revision": self.revision,
                "date_raw": 53146824,
                "paused": self.paused,
                "speed": self.speed,
                "active_event": (
                    {"instance_id": 7, "option_count": 4}
                    if self.active
                    else None
                ),
                "played_character": {"character_id": 27664},
            }

        def execute_step(
            self, step: str, *, expected_revision: int | None = None
        ) -> dict[str, object]:
            if step == "pause-map":
                assert expected_revision == self.revision
                self.paused = True
            else:
                assert step == "set-speed-1"
                assert expected_revision is None
                self.speed = 1
            self.steps.append(step)
            self.revision += 1
            return {"step": step, "accepted": True, "status": "submitted"}

        def query_current_event_window_context_v1(
            self, event_instance_id: int, *, expected_revision: int
        ) -> dict[str, object]:
            assert self.active is True
            self.query_calls.append((event_instance_id, expected_revision))
            return {
                "status": "available",
                "current_event_window_context": {
                    "event_definition_key": "zg361.6",
                    "readiness": {
                        "event_definition_identity_ready": True,
                        "option_presentation_ready": True,
                    },
                    "options": [
                        {
                            "native_option_index": 0,
                            "shown": True,
                            "enabled": True,
                            "resolved_name": "最后申诉！要求复核！",
                        },
                        {
                            "native_option_index": 1,
                            "shown": True,
                            "enabled": True,
                            "resolved_name": "散尽家财，上下打点。",
                        },
                        {
                            "native_option_index": 2,
                            "shown": True,
                            "enabled": True,
                            "resolved_name": "认命致仕，体面退场。",
                        },
                        {
                            "native_option_index": 3,
                            "shown": True,
                            "enabled": True,
                            "resolved_name": "掀桌起兵！（建立独立派系，对抗主君）",
                        },
                    ],
                },
            }

        def select_event_option(
            self,
            option_number: int,
            *,
            event_instance_id: int | None = None,
            expected_revision: int | None = None,
        ) -> dict[str, object]:
            assert self.paused is True
            assert self.active is True
            self.selections.append(
                (option_number, event_instance_id, expected_revision)
            )
            self.active = False
            self.revision += 1
            return {
                "step": f"select-event-option-{option_number}",
                "accepted": True,
                "status": "submitted",
            }

    split_elimination_items = event_frame(
        "你被列入末位淘汰名单",
        (
            ("最后申诉！要求复核！", (930, 887)),
            ("认命致仕，体面退场。", (930, 989)),
            ("掀桌起兵！", (808, 1043)),
            ("（建立独立派系，对抗主君）", (983, 1043)),
        ),
    )
    split_elimination_image = FakeDesktopImage(split_elimination_items)
    _split_lower, split_selected = real_select(
        [dict(item) for item in split_elimination_items],
        split_elimination_image,
        allow_succession=False,
    )
    assert split_selected is not None
    split_preferred_title, split_preferred_option = (
        capture.promo_preferred_product_event_option(
            split_elimination_items, 2560, 1440
        )
    )
    assert split_preferred_title == "你被列入末位淘汰名单"
    assert split_preferred_option is not None
    assert split_preferred_option["text"] == "掀桌起兵！"

    with tempfile.TemporaryDirectory() as temporary:
        artifacts = Path(temporary)
        resolved_product_service = NativeResolvedProductService()

        def resolved_product_grab() -> FakeDesktopImage:
            return FakeDesktopImage(
                [dict(item) for item in split_elimination_items]
                if resolved_product_service.active
                else []
            )

        with (
            mock.patch.object(capture.acceptance, "focus_ck3"),
            mock.patch.object(
                capture.acceptance.ImageGrab,
                "grab",
                side_effect=resolved_product_grab,
            ),
            mock.patch.object(
                capture.acceptance,
                "ocr_box_results",
                side_effect=lambda image, _region: [
                    dict(item) for item in image.items
                ],
            ),
            mock.patch.object(
                capture.acceptance,
                "write_recovery_bundle",
                side_effect=write_fake_bundle,
            ),
            mock.patch.object(
                capture.acceptance,
                "quick_recovery_kind",
                return_value=None,
            ),
            mock.patch.object(capture.acceptance, "deliberate_click") as click,
            mock.patch.object(
                capture.time, "monotonic", side_effect=advancing_clock()
            ),
            mock.patch.object(capture.time, "sleep"),
        ):
            resolved_product_dismissed = capture.settle_promo_interruptions(
                artifacts,
                "mock_split_elimination",
                observation_s=0.0,
                stop_event_title="KPI 分项证据单",
                stop_event_definition_key="zg361m.1",
                native_event_service=resolved_product_service,
            )
        click.assert_not_called()
        assert resolved_product_service.steps == ["pause-map", "set-speed-1"]
        assert resolved_product_service.selections == [(4, 7, 62)]
        assert len(resolved_product_dismissed) == 1
        resolved_product_row = resolved_product_dismissed[0]
        assert resolved_product_row["selection_method"] == (
            "native_mcp_resolved_product_option"
        )
        assert resolved_product_row["native_event_definition_key"] == "zg361.6"
        resolved_product_gate = resolved_product_row["native_selection_evidence"]
        assert resolved_product_gate["result"] == "GREEN"
        assert resolved_product_gate["native_option_selection"]["result"] == (
            "GREEN"
        )
        assert resolved_product_gate["native_option_selection"][
            "selected_native_option_index"
        ] == 3
        assert resolved_product_gate["native_option_selection"][
            "selected_option_number"
        ] == 4

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

    centered_letter_items = [
        event_item("A former servant writes", (1235, 502), 190),
        event_item(
            "The letter contains a sufficiently wide narrative line",
            (1280, 600),
            900,
        ),
        event_item("Traitor!", (1280, 985), 160),
    ]
    centered_letter_image = FakeDesktopImage(centered_letter_items)
    _lower, centered_letter_selected = real_select(
        [dict(item) for item in centered_letter_items],
        centered_letter_image,
        allow_succession=False,
    )
    assert centered_letter_selected is not None
    assert capture.promo_event_modal_evidence(
        centered_letter_items, 2560, 1440
    ) is False
    assert capture.acceptance.quick_recovery_kind(
        centered_letter_items,
        centered_letter_selected,
        2560,
        1440,
    ) == "center_event_option"

    class NativeSingleOptionService:
        def __init__(self) -> None:
            self.paused = False
            self.cleared = False
            self.revision = 20
            self.steps: list[tuple[str, int | None]] = []
            self.selections: list[tuple[int, int | None, int | None]] = []

        def snapshot(self) -> dict[str, object]:
            return {
                "revision": self.revision,
                "native_revision": self.revision,
                "date_raw": 53144688,
                "paused": self.paused,
                "speed": 5,
                "active_event": (
                    None
                    if self.cleared
                    else {"instance_id": 5, "option_count": 1}
                ),
            }

        def execute_step(
            self, step: str, *, expected_revision: int | None = None
        ) -> dict[str, object]:
            assert step == "pause-map"
            assert expected_revision == self.revision
            self.steps.append((step, expected_revision))
            self.paused = True
            self.revision += 1
            return {
                "step": step,
                "accepted": True,
                "status": "submitted",
            }

        def select_event_option(
            self,
            option_number: int,
            *,
            event_instance_id: int | None = None,
            expected_revision: int | None = None,
        ) -> dict[str, object]:
            assert self.paused is True
            assert self.cleared is False
            assert option_number == 1
            assert event_instance_id == 5
            assert expected_revision == self.revision
            self.selections.append(
                (option_number, event_instance_id, expected_revision)
            )
            self.cleared = True
            self.revision += 1
            return {
                "step": "select-event-option-1",
                "accepted": True,
                "status": "submitted",
            }

    native_single = NativeSingleOptionService()

    def native_letter_grab() -> FakeDesktopImage:
        return FakeDesktopImage(
            []
            if native_single.cleared
            else [dict(item) for item in centered_letter_items]
        )

    with tempfile.TemporaryDirectory() as temporary:
        artifacts = Path(temporary)
        with (
            mock.patch.object(capture.acceptance, "focus_ck3"),
            mock.patch.object(
                capture.acceptance.ImageGrab, "grab", native_letter_grab
            ),
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
                return_value=(389362, (0, 0)),
            ),
            mock.patch.object(
                capture.acceptance,
                "write_recovery_bundle",
                side_effect=write_fake_bundle,
            ),
            mock.patch.object(capture.acceptance, "deliberate_click") as click,
            mock.patch.object(capture.time, "sleep"),
        ):
            native_dismissed = capture.settle_promo_interruptions(
                artifacts,
                "mock_native_letter",
                observation_s=0.0,
                native_event_service=native_single,
                native_active_event_instance_id=5,
                native_active_event_option_count=1,
            )
        click.assert_not_called()
        assert native_single.steps == [("pause-map", 20)]
        assert native_single.selections == [(1, 5, 21)]
        assert len(native_dismissed) == 1
        assert native_dismissed[0]["selection_method"] == (
            "native_mcp_single_option"
        )
        assert native_dismissed[0]["native_active_event_instance_id"] == 5
        native_gate = json.loads(
            (
                artifacts
                / "mock_native_letter_interruption_01_native_single_option_gate.json"
            ).read_text(encoding="utf-8")
        )
        assert native_gate["result"] == "GREEN"
        assert native_gate["before"]["active_event_option_count"] == 1
        assert native_gate["after"]["active_event_instance_id"] is None
        native_decision = json.loads(
            (
                artifacts / "mock_native_letter_interruption_01_decision.json"
            ).read_text(encoding="utf-8")
        )
        assert native_decision["selection_method"] == "native_mcp_single_option"
        assert native_decision["native_active_event_instance_id"] == 5

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
    for token in (
        'expected_event_definition_key="zg361.50"',
        "accept_zhongguo_result_case_snapshot_v1_live_cell",
        '"result_case_snapshot_v1_live_cell": (',
        "result_case_snapshot_live_cell",
        'expected_option_text="拒绝签收"',
        'expected_event_definition_key="zg361.4"',
        'expected_option_text="认命"',
        "select_resolved_event_option_native",
        "pause_after_promo_event_click",
        "wait_for_fixture_marker_native",
        "phase2_refused_notice_witnessed_and_settled",
        '"ocr_used_for_navigation_or_green": False',
    ):
        assert token in personal_body, token
    notice_identity_index = personal_body.index(
        'expected_event_definition_key="zg361.50"'
    )
    result_case_snapshot_index = personal_body.index(
        "accept_zhongguo_result_case_snapshot_v1_live_cell"
    )
    refusal_option_index = personal_body.index('expected_option_text="拒绝签收"')
    result_identity_index = personal_body.index(
        'expected_event_definition_key="zg361.4"'
    )
    assert (
        notice_identity_index
        < result_case_snapshot_index
        < refusal_option_index
        < result_identity_index
    )
    assert personal_body.index('expected_event_definition_key="zg361.4"') < (
        personal_body.index('("上司考定", "你的绩效", "KPI", "同组位次")')
    )
    assert "PROMO_PERSONAL_RESULT_FIELD_REGION" in personal_body
    assert '("你的绩效", "3.25")' in personal_body
    assert '("3.75", "3.5", "zg361_"' in personal_body
    assert "personal result must render exactly one grade" not in personal_body
    assert "grades = tuple" not in personal_body

    native_event_wait = inspect.getsource(capture.wait_for_native_event_definition)
    for token in (
        "pause_bound_native_event_for_definition_query",
        "query_event_definition_identity",
        "select_single_option_interruption_native",
        "resume_personal_switch_timeline_native",
        '"ocr_used_for_navigation": False',
        '"visual_fallback_used": False',
    ):
        assert token in native_event_wait, token
    assert "wait_for_ocr" not in native_event_wait
    assert "deliberate_click" not in native_event_wait

    native_marker_wait = inspect.getsource(capture.wait_for_fixture_marker_native)
    assert "stream.count(marker)" in native_marker_wait
    assert 'service.execute_step(\n                        "pause-map"' in native_marker_wait
    assert "resume_personal_switch_timeline_native" in native_marker_wait
    assert '"ocr_used_for_navigation": False' in native_marker_wait
    assert "wait_for_ocr" not in native_marker_wait
    assert "deliberate_click" not in native_marker_wait

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
        'active_event_option_count = observed["active_event_option_count"]',
        "native_event_service=timeline_service",
        "native_active_event_instance_id=active_event_id",
        "native_active_event_option_count=active_event_option_count",
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

    policy_dispatch_marker = "ZGA: TEST PASS clean_policy_001_dispatched"

    class PolicyDispatchStream:
        marker_ready = False

        def pump(self) -> None:
            return None

        def count(self, marker: str) -> int:
            assert marker == policy_dispatch_marker
            return int(self.marker_ready)

    class PolicyDispatchService:
        def __init__(self) -> None:
            self.revision = 1
            self.date_raw = 200
            self.paused = True
            self.speed = 5
            self.active_event: dict[str, int] | None = None

        def snapshot(self) -> dict[str, object]:
            return {
                "revision": self.revision,
                "native_revision": self.revision,
                "date_raw": self.date_raw,
                "paused": self.paused,
                "speed": self.speed,
                "active_event": self.active_event,
            }

    policy_stream = PolicyDispatchStream()
    policy_service = PolicyDispatchService()
    policy_actions: list[str] = []
    policy_resume_reasons: list[str] = []
    policy_settle_calls: list[dict[str, object]] = []

    def fake_policy_resume(_service, *, reason, timeout_s=10.0):
        del timeout_s
        assert _service is policy_service
        policy_resume_reasons.append(reason)
        policy_actions.append(f"resume:{reason}")
        policy_service.revision += 1
        if len(policy_resume_reasons) == 1:
            # The shipped 3.25 elimination follow-up reaches the modal first.
            policy_service.date_raw += 2
            policy_service.paused = True
            policy_service.active_event = {"instance_id": 6, "option_count": 4}
        else:
            policy_service.date_raw += 1
            policy_service.paused = False
            policy_service.active_event = None
            policy_stream.marker_ready = True
        return {"reason": reason, "result": "GREEN"}

    def fake_policy_settle(_artifacts, stem, **kwargs):
        assert _artifacts == policy_artifacts
        assert policy_service.active_event == {"instance_id": 6, "option_count": 4}
        policy_actions.append("settle:zg361.6")
        policy_settle_calls.append({"stem": stem, **kwargs})
        policy_service.revision += 1
        policy_service.paused = True
        policy_service.active_event = None
        return [{"event_definition_key": "zg361.6", "selection": "preferred"}]

    with tempfile.TemporaryDirectory() as temp_dir:
        policy_artifacts = Path(temp_dir)
        with mock.patch.object(
            capture,
            "resume_personal_switch_timeline_native",
            side_effect=fake_policy_resume,
        ), mock.patch.object(
            capture,
            "settle_promo_interruptions",
            side_effect=fake_policy_settle,
        ), mock.patch.object(
            capture.time, "monotonic", return_value=0.0
        ), mock.patch.object(capture.time, "sleep", return_value=None):
            policy_interruptions = capture.advance_to_policy_dispatch(
                policy_stream,
                policy_artifacts,
                timeline_service=policy_service,
                stem="12_policy_001",
                dispatch_marker=policy_dispatch_marker,
                target_event_title="policy #001",
                target_event_definition_key="zg361m.1",
                timeout_s=1.0,
            )

        assert policy_interruptions == [
            {"event_definition_key": "zg361.6", "selection": "preferred"}
        ]
        assert policy_actions == [
            "resume:12_policy_001_initial_resume",
            "settle:zg361.6",
            "resume:12_policy_001_resume_after_01",
        ]
        assert policy_resume_reasons == [
            "12_policy_001_initial_resume",
            "12_policy_001_resume_after_01",
        ]
        assert len(policy_settle_calls) == 1
        assert policy_settle_calls[0]["native_active_event_instance_id"] == 6
        assert policy_settle_calls[0]["native_active_event_option_count"] == 4
        assert policy_settle_calls[0]["stop_event_definition_key"] == "zg361m.1"
        assert policy_settle_calls[0]["stop_event_title"] == "policy #001"
        assert policy_stream.marker_ready is True
        policy_gate = json.loads(
            (
                policy_artifacts
                / "12_policy_001_dispatch_timeline_gate.json"
            ).read_text(encoding="utf-8")
        )
        assert policy_gate["result"] == "GREEN"
        assert policy_gate["dispatch_marker_count"] == 1
        assert policy_gate["interruption_count"] == 1
        assert len(policy_gate["native_resumes"]) == 2
        assert any(
            row["active_event_instance_id"] == 6
            for row in policy_gate["native_observations"]
        )

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
