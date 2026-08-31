from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_zhongguo_scoreboard_state_v1,
)
from xar_autoplayer.bridge.zhongguo_scoreboard_state_contract import (
    QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY,
    QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP,
    ZHONGGUO_SCOREBOARD_STATE_V1_ALLOWLIST_ID,
    ZHONGGUO_SCOREBOARD_STATE_V1_BACKEND_ID,
    ZHONGGUO_SCOREBOARD_STATE_V1_CONSUMER_ID,
    ZHONGGUO_SCOREBOARD_STATE_V1_EXECUTABLE_SHA256,
    ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION,
    normalize_native_zhongguo_scoreboard_state_v1,
    parse_query_zhongguo_scoreboard_state_v1_step,
    query_zhongguo_scoreboard_state_v1_step,
)


REVISION = 77
DATE_RAW = 4242
PLAYER = 101
NONCE = "scoreboard.batch-01"
SCHEMA = PROJECT_ROOT / "schemas/zhongguo-scoreboard-state-v1.schema.json"


def typed(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def unavailable(reason: str) -> dict[str, object]:
    return {"status": "unavailable", "value": None, "unavailable_reason": reason}


def widget(stable: str, runtime: str, *, visible: bool) -> dict[str, object]:
    return {
        "stable_identity": stable,
        "runtime_name": runtime,
        "exists": typed(True),
        "local_visible": typed(visible),
        "effective_visible": typed(visible),
        "enabled": unavailable(
            "named_clickable_child_not_stable"
            if stable == "zg361_open_scoreboard"
            else "enabled_state_abi_not_frozen"
        ),
        "focused": unavailable("focus_owner_abi_not_frozen"),
        "modal_blocking": unavailable("modal_blocking_abi_not_frozen"),
        "screen_x": unavailable("screen_rect_abi_not_frozen"),
        "screen_y": unavailable("screen_rect_abi_not_frozen"),
        "screen_width": unavailable("screen_rect_abi_not_frozen"),
        "screen_height": unavailable("screen_rect_abi_not_frozen"),
        "scroll_min": unavailable("scroll_area_extent_abi_not_frozen"),
        "scroll_max": unavailable("scroll_area_extent_abi_not_frozen"),
        "scroll_value": unavailable("scroll_area_extent_abi_not_frozen"),
    }


def native_frame() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "available",
        "case_kind": "zhongguo.scoreboard.named-state-acl",
        "request_nonce": NONCE,
        "snapshot_revision": REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": PLAYER,
        "widgets": [
            widget("zg361_open_scoreboard", "zg361_scoreboard_toggle", visible=True),
            widget("zg361_scoreboard_window", "zg361_scoreboard_window", visible=True),
            widget("zg361_scoreboard_modal", "zg361_scoreboard_modal", visible=False),
            widget("zg361_scoreboard_panel", "zg361_scoreboard_panel", visible=False),
        ],
        "acl": {
            "managed": {
                "surface_available": False,
                "current_player_can_assess_others": False,
                "owner_character_id": unavailable("surface_not_available"),
                "first_subject_character_id": unavailable("surface_not_available"),
            },
            "received_self": {
                "surface_available": True,
                "current_player_is_subject": True,
                "first_row_character_id": typed(PLAYER),
                "owner_character_id": typed(202),
                "subject_character_id": typed(PLAYER),
                "cycle_serial": typed(8),
                "result_case_serial": typed(903),
                "b1_case_serial": typed(41),
                "disclosure_acl_mode": typed(3),
                "disclosure_policy_available": typed(1),
                "disclosure_policy_id": typed(41),
                "disclosure_self_mode": typed(3),
                "disclosure_team_mode": typed(2),
                "disclosure_evaluator_identity_mode": typed(0),
                "disclosure_blackbox_risk": typed(1),
            },
        },
        "actions": {
            "activate": unavailable("read_only_provider_action_not_exposed"),
            "close": unavailable("read_only_provider_action_not_exposed"),
            "reopen": unavailable("read_only_provider_action_not_exposed"),
        },
        "readiness": {
            "player_binding_ready": True,
            "gui_root_ready": True,
            "entry_window_state_ready": True,
            "acl_ready": True,
            "same_frame_ready": True,
            "state_acl_query_ready": True,
            "full_widget_gate_ready": False,
            "production_live_ready": False,
        },
        "unavailable_reason": None,
        "provenance": {
            "game_version": ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION,
            "executable_sha256": ZHONGGUO_SCOREBOARD_STATE_V1_EXECUTABLE_SHA256,
            "backend_id": ZHONGGUO_SCOREBOARD_STATE_V1_BACKEND_ID,
            "consumer_id": ZHONGGUO_SCOREBOARD_STATE_V1_CONSUMER_ID,
            "allowlist_id": ZHONGGUO_SCOREBOARD_STATE_V1_ALLOWLIST_ID,
            "gui_global_slot_rva": "0x576CC68",
            "find_top_level_widget_rva": "0x36D0B20",
            "widget_hidden_flags_offset": "0xD0",
            "widget_parent_offset": "0xE8",
            "widget_children_offset": "0xF0",
            "widget_name_offset": "0x1B8",
            "query_scope": "fixed_scoreboard_instances_and_player_frozen_acl",
            "contract_stage": "static_exact_build_live_unverified",
        },
    }


class ZhongguoScoreboardStateContractTests(unittest.TestCase):
    def test_step_is_nonce_only_and_rejects_arbitrary_widget_names(self) -> None:
        step = query_zhongguo_scoreboard_state_v1_step(NONCE)
        query = parse_query_zhongguo_scoreboard_state_v1_step(step)
        self.assertIsNotNone(query)
        assert query is not None
        self.assertEqual(query.request_nonce, NONCE)
        extended = parse_query_zhongguo_scoreboard_state_v1_step(
            f"{step}-zg361_scoreboard_window"
        )
        self.assertIsNotNone(extended)
        assert extended is not None
        self.assertEqual(
            extended.request_nonce,
            "scoreboard.batch-01-zg361_scoreboard_window",
        )
        self.assertEqual(extended.__dataclass_fields__.keys(), {"request_nonce"})
        with self.assertRaises(ValueError):
            query_zhongguo_scoreboard_state_v1_step("bad/widget")

    def test_available_frame_preserves_honest_static_boundary(self) -> None:
        query = parse_query_zhongguo_scoreboard_state_v1_step(
            query_zhongguo_scoreboard_state_v1_step(NONCE)
        )
        assert query is not None
        normalized = normalize_native_zhongguo_scoreboard_state_v1(
            native_frame(),
            expected_query=query,
            expected_snapshot_revision=REVISION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER,
        )
        self.assertTrue(normalized["readiness"]["state_acl_query_ready"])
        self.assertFalse(normalized["readiness"]["full_widget_gate_ready"])
        self.assertFalse(normalized["readiness"]["production_live_ready"])
        self.assertEqual(
            normalized["widgets"][0]["enabled"]["unavailable_reason"],
            "named_clickable_child_not_stable",
        )
        self.assertEqual(
            normalized["actions"]["activate"]["unavailable_reason"],
            "read_only_provider_action_not_exposed",
        )

    def test_identity_acl_and_action_drift_fail_closed(self) -> None:
        query = parse_query_zhongguo_scoreboard_state_v1_step(
            query_zhongguo_scoreboard_state_v1_step(NONCE)
        )
        assert query is not None
        for mutation in ("identity", "manager_acl", "action", "live"):
            with self.subTest(mutation=mutation):
                frame = native_frame()
                if mutation == "identity":
                    frame["widgets"][0]["runtime_name"] = "caller_widget"
                elif mutation == "manager_acl":
                    frame["acl"]["managed"][
                        "current_player_can_assess_others"
                    ] = True
                elif mutation == "action":
                    frame["actions"]["activate"] = typed(True)
                else:
                    frame["readiness"]["production_live_ready"] = True
                with self.assertRaises(ValueError):
                    normalize_native_zhongguo_scoreboard_state_v1(
                        frame,
                        expected_query=query,
                        expected_snapshot_revision=REVISION,
                        expected_date_raw=DATE_RAW,
                        expected_player_character_id=PLAYER,
                    )

    def test_schema_accepts_service_envelope(self) -> None:
        value = native_frame()
        value.update(
            {
                "build": {
                    "version": ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION,
                    "exe_sha256": ZHONGGUO_SCOREBOARD_STATE_V1_EXECUTABLE_SHA256,
                },
                "source": {
                    "bridge_version": "0.1.0",
                    "game_adapter_id": "ck3-1.19.0.6-msvc-x64",
                    "backend_id": "native-headless",
                    "consumer_id": ZHONGGUO_SCOREBOARD_STATE_V1_CONSUMER_ID,
                    "connection_generation": 3,
                    "query_sequence": 1,
                    "snapshot_id": "native:77",
                    "revision": 19,
                    "native_revision": REVISION,
                    "date_raw": DATE_RAW,
                    "paused": True,
                    "player_character_id": PLAYER,
                },
                "binding": {
                    "request_nonce": NONCE,
                    "snapshot_id": "native:77",
                    "revision": 19,
                    "native_revision": REVISION,
                    "connection_generation": 3,
                    "date_raw": DATE_RAW,
                    "paused": True,
                    "player_character_id": PLAYER,
                    "expected_revision": 19,
                },
            }
        )
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(value)
        invalid = copy.deepcopy(value)
        invalid["readiness"]["production_live_ready"] = True
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(invalid)

    def test_mcp_helper_exposes_no_widget_or_action_parameter(self) -> None:
        class Service:
            def query_zhongguo_scoreboard_state_v1(
                self, request_nonce: str, *, expected_revision: int
            ) -> dict[str, object]:
                return {"nonce": request_nonce, "revision": expected_revision}

        self.assertEqual(
            _ck3_query_zhongguo_scoreboard_state_v1(
                Service(), NONCE, 19  # type: ignore[arg-type]
            ),
            {"nonce": NONCE, "revision": 19},
        )

    def test_source_contract_is_fixed_and_connected(self) -> None:
        paths = {
            "header": PROJECT_ROOT
            / "native_bridge/include/xar_bridge/zhongguo_scoreboard_state_v1.hpp",
            "reader": PROJECT_ROOT
            / "native_bridge/src/zhongguo_scoreboard_state_v1.cpp",
            "mailbox": PROJECT_ROOT
            / "native_bridge/src/zhongguo_scoreboard_state_v1_mailbox.cpp",
            "bridge": PROJECT_ROOT / "native_bridge/src/bridge.cpp",
            "adapter": PROJECT_ROOT
            / "native_bridge/src/ck3_11906_adapter.cpp",
            "game_adapter": PROJECT_ROOT
            / "native_bridge/src/game_adapter.cpp",
            "service": PROJECT_ROOT
            / "src/xar_autoplayer/bridge/service.py",
            "mcp": PROJECT_ROOT
            / "src/xar_autoplayer/bridge/mcp_server.py",
            "gui": REPO_ROOT / "mod_zhongguo_style/gui/zg361_scoreboard.gui",
        }
        sources = {
            name: path.read_text(encoding="utf-8-sig")
            for name, path in paths.items()
        }
        for identity in (
            "zg361_scoreboard_toggle",
            "zg361_scoreboard_window",
            "zg361_scoreboard_modal",
            "zg361_scoreboard_panel",
        ):
            self.assertIn(identity, sources["header"])
            self.assertIn(f'name = "{identity}"', sources["gui"])
        for key in (
            "zg361_sb_m_01_char",
            "zg361_scoreboard_managed_owner",
            "zg361_sb_r_01_char",
            "zg361_sb_self_char",
            "zg361_sb_self_disclosure_acl_mode",
        ):
            self.assertIn(key, sources["header"])
        self.assertIn(QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP, sources["bridge"])
        self.assertIn("kZhongguoScoreboardStateV1Capability", sources["adapter"])
        self.assertIn("ParseZhongguoScoreboardStateV1Step", sources["game_adapter"])
        self.assertIn("QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP", sources["service"])
        self.assertIn("ck3_query_zhongguo_scoreboard_state_v1", sources["mcp"])
        self.assertNotIn("activate_named_scripted_widget", sources["mcp"])
        self.assertNotIn("widget_name: str", sources["mcp"])
        self.assertIn(
            "kZhongguoScoreboardStateV1Capability",
            sources["adapter"],
        )


if __name__ == "__main__":
    unittest.main()
