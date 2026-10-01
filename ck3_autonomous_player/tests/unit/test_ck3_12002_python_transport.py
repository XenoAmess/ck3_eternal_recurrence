"""Offline regression for the delivered 1.20 wire on the advanced Python tree."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ck3_autonomous_player.tests.unit import test_title_map_navigation_v1_bridge as title
from ck3_autonomous_player.tests.unit import test_campaign_root_context_v1_bridge as campaign_fixture
from ck3_autonomous_player.tests.unit import test_prewar_scope_contract as prewar_fixture
from ck3_autonomous_player.tests.unit import test_war_entry_contract as entry_fixture
from ck3_autonomous_player.tests.unit import test_war_termination_terms_contract as terms_fixture
from xar_autoplayer.bridge.campaign_root_context_contract import (
    normalize_campaign_root_context_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.prewar_scope_contract import normalize_prewar_primary_scope
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import (
    CK3_11906, CK3_12002, require_exact_native_build,
)
from xar_autoplayer.bridge.war_contract import (
    normalize_war_termination_terms, normalize_war_termination_options,
)
from xar_autoplayer.bridge.war_entry_contract import normalize_war_entry_assessments


def _new_source(suffix: str) -> dict[str, str]:
    return {
        "game_version": CK3_12002.game_version,
        "executable_sha256": CK3_12002.executable_sha256,
        "backend_id": CK3_12002.backend_id(suffix),
    }


def _new_title_hello() -> dict[str, object]:
    hello = title._hello()
    hello.update(
        game_version=CK3_12002.game_version,
        expected_ck3_version=CK3_12002.game_version,
        executable_sha256=CK3_12002.executable_sha256,
        expected_ck3_sha256=CK3_12002.executable_sha256,
    )
    return hello


class _NewTitleServiceDriver(title._ServiceDriver):
    def take_snapshot(self) -> dict[str, object]:
        snapshot = super().take_snapshot()
        snapshot["diagnostics"]["hello"] = _new_title_hello()
        return snapshot

    def center_map_on_landed_title_v1(self, title_key, *, expected_revision):
        result = super().center_map_on_landed_title_v1(
            title_key, expected_revision=expected_revision,
        )
        result["source"] = _new_source("title-map-navigation-v1")
        return result


def _baseline_campaign() -> dict[str, object]:
    return {
        "schema_version": 1, "status": "available", "snapshot_revision": 17,
        "date_raw": title.DATE_RAW, "local_player_id": 0,
        "player_character_id": title.PLAYER_CHARACTER_ID,
        "player_character_alive": True,
        "primary_title": {"title_id": 1234, "tier_raw": 3, "tier_key": "duchy"},
        "capital_province_id": 42, "immediate_liege_character_id": None,
        "top_liege_character_id": title.PLAYER_CHARACTER_ID, "independent": True,
        "government": {"key": "feudal_government", "flags": [], "native_flag_count": 0},
        "selected_game_rule_tokens": [], "native_selected_game_rule_token_count": 0,
        "readiness": {key: True for key in (
            "player_identity_ready", "primary_title_ready", "capital_ready",
            "lieges_ready", "government_ready", "selected_game_rule_tokens_ready",
            "same_frame_ready", "ready",
        )},
        "unavailable_reason": None,
        "provenance": {
            **_new_source("campaign-root-context-v1"),
            "primary_title_rva": "0x289DA30", "capital_province_rva": "0x28B1CD0",
            "immediate_liege_rva": "0x28BFC70", "top_liege_rva": "0x28BFDA0",
            "government_rva": "0x28C2E10", "selected_game_rule_service_slot_rva": "0x5CB3D78",
        },
    }


class Ck3NewBuildTransportTests(unittest.TestCase):
    def test_exact_identity_preserves_both_versions(self):
        for build in (CK3_11906, CK3_12002):
            self.assertEqual(require_exact_native_build(
                build.game_version, build.executable_sha256.lower(),
            ), build)

    def test_new_title_driver_uses_separate_typed_key_and_native_revision(self):
        endpoint = title._FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint)
        endpoint.publish(_new_title_hello())
        endpoint.publish(title._semantic_snapshot())
        result = title._raw_result()
        result["source"] = _new_source("title-map-navigation-v1")
        title._answer_with(endpoint, lambda: copy.deepcopy(result))
        revision = int(driver.take_snapshot()["revision"])
        actual = driver.center_map_on_landed_title_v1("c_bianzhou", expected_revision=revision)
        self.assertEqual(actual["source"]["game_version"], "1.20.0.2")
        frame = title._execute_frames(endpoint)[0]
        self.assertEqual(frame["title_key"], "c_bianzhou")
        self.assertEqual(frame["expected_revision"], title.NATIVE_REVISION)

    def test_title_result_must_match_the_hello_build(self):
        endpoint = title._FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint)
        endpoint.publish(_new_title_hello())
        endpoint.publish(title._semantic_snapshot())
        title._answer_with(endpoint, title._raw_result)
        with self.assertRaisesRegex(BridgeUnavailableError, "build mirror"):
            driver.center_map_on_landed_title_v1(
                "c_bianzhou", expected_revision=int(driver.take_snapshot()["revision"]),
            )

    def test_baseline_campaign_does_not_invent_extended_observations(self):
        frame = _baseline_campaign()
        result = normalize_campaign_root_context_v1(
            frame, expected_date_raw=title.DATE_RAW, expected_snapshot_revision=17,
        )
        self.assertEqual(result, frame)
        self.assertNotIn("player_health", result)
        self.assertNotIn("player_health_ready", result["readiness"])

    def test_baseline_campaign_crosses_native_driver_and_public_service(self):
        endpoint = title._FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint)
        hello = _new_title_hello()
        hello["capabilities"] = ["game.state.snapshot", campaign_fixture.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY]
        endpoint.publish(hello)
        endpoint.publish(title._semantic_snapshot())
        raw = campaign_fixture._native_result()
        raw["campaign_root_context"] = _baseline_campaign()
        title._answer_with(endpoint, lambda: copy.deepcopy(raw))
        service = GameplayBridgeService(driver)
        revision = int(service.snapshot()["revision"])
        result = service.query_campaign_root_context_v1(expected_revision=revision)
        self.assertEqual(result["build"]["version"], "1.20.0.2")
        self.assertNotIn("player_health", result)
        self.assertNotIn("player_health_ready", result["readiness"])

    def test_extended_campaign_preserves_newly_mapped_nonwar_observations(self):
        frame = campaign_fixture._frame()
        frame["provenance"] = {
            **_baseline_campaign()["provenance"],
            "monthly_gold_income_rva": "0x2BCA960", "character_health_rva": "0x28C6500",
            "domain_size_rva": "0x28B7200", "domain_limit_rva": "0x28B71D0",
            "has_targeting_faction_trigger_rva": "0x2B250D0",
            "council_position_lookup_rva": "0x2684F00",
            "council_active_task_ids_enumerator_rva": "0x2916CE0",
            "council_active_task_storage_slot_rva": "0x5D1DEA0",
            "council_value_progress_current_rva": "0x31AB520",
            "council_value_progress_maximum_rva": "0x31AB840",
            "held_title_ids_offset": "0x1E0", "title_province_rva": "0x230F900",
            "province_holder_character_id_rva": "0x247D030",
        }
        result = normalize_campaign_root_context_v1(
            frame, expected_date_raw=title.DATE_RAW, expected_snapshot_revision=17,
        )
        self.assertEqual(result["player_health"], frame["player_health"])
        self.assertEqual(result["council"], frame["council"])
        self.assertEqual(result["primary_title_succession_character_ids"], frame["primary_title_succession_character_ids"])
        self.assertTrue(result["readiness"]["player_health_ready"])

    def test_legacy_extended_campaign_cannot_be_confused_with_new_baseline(self):
        frame = _baseline_campaign()
        frame["provenance"]["game_version"] = CK3_11906.game_version
        with self.assertRaises(ValueError):
            normalize_campaign_root_context_v1(
                frame, expected_date_raw=title.DATE_RAW, expected_snapshot_revision=17,
            )

    def test_prewar_observation_uses_new_storage_without_claiming_forecast(self):
        frame = prewar_fixture._payload()
        frame["provenance"].update(
            game_version=CK3_12002.game_version,
            executable_sha256=CK3_12002.executable_sha256,
            unit_storage_slot_rva="0x5D1E380",
        )
        actual = normalize_prewar_primary_scope(
            frame, expected_declaration_id=frame["declaration_id"],
            expected_actor_character_id=frame["actor_character_id"],
        )
        self.assertEqual(actual["provenance"]["unit_storage_slot_rva"], "0x5D1E380")
        self.assertFalse(actual["readiness"]["war_entry_forecast_inputs_ready"])

    def test_war_entry_keeps_native_power_decomposition_on_new_build(self):
        frame = entry_fixture._payload()
        frame["provenance"] = {
            "game_version": CK3_12002.game_version, "executable_sha256": CK3_12002.executable_sha256,
            "assessment_rva": "0x1A23240", "network_collector_rva": "0x1A24010",
            "power_leaf": "CCharacter+0x1C0->+0x308", "fixed_point_scale": 100000,
        }
        actual = normalize_war_entry_assessments(frame)
        self.assertEqual(actual["assessments"], frame["assessments"])

    def test_claim_terms_support_new_binding_without_relabeling_event_war_slice(self):
        frame = terms_fixture._available_terms()
        frame["provenance"].update(
            game_version=CK3_12002.game_version,
            executable_sha256=CK3_12002.executable_sha256,
            native_reader="CWar+0x270/+0x290;0x2B9ECD0",
            claim_script_sha256="887BF0197401CB17CB4588978ADD556AB6B429BF55CB482E3E5F2D0E8351CFD4",
        )
        self.assertEqual(normalize_war_termination_terms(frame), frame)
        legacy_event = terms_fixture._available_raiktor_terms()
        legacy_event["provenance"].update(
            game_version=CK3_12002.game_version,
            executable_sha256=CK3_12002.executable_sha256,
        )
        with self.assertRaisesRegex(ValueError, "not closed"):
            normalize_war_termination_terms(legacy_event)

    def test_recorded_new_war_options_keep_final_recipient_response_unavailable(self):
        fixture = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "war_termination_options_12002_replay.json").read_text(encoding="utf-8"))
        source = require_exact_native_build(
            fixture["build"]["version"], fixture["build"]["exe_sha256"],
        )
        frame = fixture["war_termination_options"]
        result = normalize_war_termination_options(frame, source_build=source)
        for name, option in frame["options"].items():
            self.assertEqual(result["options"][name]["recipient_response"], {
                "status": "unavailable", "decision_status_raw": None,
                "would_accept_now": None,
            })
            self.assertEqual(result["options"][name]["auto_accept"], option["auto_accept"])
            self.assertEqual(result["options"][name]["ai_acceptance"], option["ai_acceptance"])
        with self.assertRaises(ValueError):
            normalize_war_termination_options(frame)
        with self.assertRaises(ValueError):
            normalize_war_termination_options(frame, source_build=CK3_11906)


class NewBuildMcpMemoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_sdk_calls_newbuild_typed_title_tool_in_memory(self):
        from mcp import Client

        driver = _NewTitleServiceDriver()
        async with Client(create_server(driver)) as client:
            listed = await client.list_tools()
            self.assertIn("ck3_center_map_on_landed_title_v1", {tool.name for tool in listed.tools})
            result = await client.call_tool("ck3_center_map_on_landed_title_v1", {
                "title_key": "c_bianzhou", "expected_revision": title.PUBLIC_REVISION,
            })
        self.assertFalse(result.is_error)
        self.assertEqual(result.structured_content["source"]["game_version"], "1.20.0.2")
        self.assertEqual(driver.typed_calls, [("c_bianzhou", title.PUBLIC_REVISION)])


if __name__ == "__main__":
    unittest.main()
