"""Offline wire replay for both frozen CK3 adapter identities."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_title_map_navigation_v1_bridge as title_fixture
import test_war_entry_contract as war_entry_fixture
import test_pending_character_interaction_context_v1_bridge as pending_fixture
import test_prewar_scope_contract as prewar_fixture
import test_loaded_feature_manifest_v1_bridge as feature_fixture
import test_war_termination_terms_contract as terms_fixture
import test_campaign_root_context_v1_bridge as campaign_fixture

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.title_map_navigation_contract import (
    normalize_native_title_map_navigation_v1_result,
)
from xar_autoplayer.bridge.version_identity import (
    CK3_11906,
    CK3_12002,
    require_exact_native_backend,
    require_exact_native_build,
)
from xar_autoplayer.bridge.war_entry_contract import (
    normalize_war_entry_assessments,
)
from xar_autoplayer.bridge.event_window_context_contract import (
    normalize_current_event_window_context_v1,
)
from xar_autoplayer.bridge.pending_character_interaction_context_contract import (
    normalize_pending_character_interaction_context_v1,
)
from xar_autoplayer.bridge.prewar_scope_contract import (
    PREWAR_SCOPE_V1_ADVERTISED,
    normalize_prewar_primary_scope,
)
from xar_autoplayer.bridge.loaded_feature_manifest_contract import (
    normalize_loaded_feature_manifest_v1,
)
from xar_autoplayer.bridge.war_contract import normalize_war_termination_terms
from xar_autoplayer.bridge.campaign_root_context_contract import (
    normalize_campaign_root_context_v1,
)

EVENT_INSTANCE_ID = 16_777_257
EVENT_DATE_RAW = 741_221
EVENT_NATIVE_REVISION = 17


def _new_event_frame():
    fixture = PROJECT_ROOT / "tests/fixtures/ck3_12002_event_window_native.json"
    return json.loads(fixture.read_text(encoding="utf-8-sig"))


def _old_event_provenance():
    return {
        "root": "module+0x570F7B8->+0x10",
        "idler_vtable_rva": "0x40B1D30",
        "manager_offset": "+0x28",
        "backend_id": CK3_11906.backend_id("event-window-v1"),
    }


def _title_source(build) -> dict[str, str]:
    return {
        "game_version": build.game_version,
        "executable_sha256": build.executable_sha256,
        "backend_id": build.backend_id("title-map-navigation-v1"),
    }


def _title_result(build) -> dict[str, object]:
    frame = title_fixture._raw_result()
    frame["source"] = _title_source(build)
    return frame


def _hello(build) -> dict[str, object]:
    frame = title_fixture._hello()
    frame.update(
        game_version=build.game_version,
        expected_ck3_version=build.game_version,
        executable_sha256=build.executable_sha256,
        expected_ck3_sha256=build.executable_sha256,
    )
    return frame


def _driver(build):
    endpoint = title_fixture._FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.05,
    )
    endpoint.publish(_hello(build))
    endpoint.publish(title_fixture._semantic_snapshot())
    return driver, endpoint


class _TitleServiceDriver(title_fixture._ServiceDriver):
    def __init__(self, hello_build, result_build):
        super().__init__()
        self.hello_build = hello_build
        self.result_build = result_build

    def take_snapshot(self):
        frame = super().take_snapshot()
        frame["diagnostics"]["hello"] = _hello(self.hello_build)
        return frame

    def center_map_on_landed_title_v1(self, title_key, *, expected_revision):
        frame = super().center_map_on_landed_title_v1(
            title_key, expected_revision=expected_revision,
        )
        frame["source"] = _title_source(self.result_build)
        return frame


class NativeBuildWireReplayTests(unittest.TestCase):
    def test_frozen_build_pairs_keep_old_and_new_identity_separate(self):
        for build in (CK3_11906, CK3_12002):
            with self.subTest(version=build.game_version):
                self.assertEqual(
                    require_exact_native_build(
                        build.game_version, build.executable_sha256.lower(),
                    ),
                    build,
                )
                self.assertEqual(
                    require_exact_native_backend(
                        build.game_version, build.executable_sha256,
                        build.backend_id("title-map-navigation-v1"),
                        suffix="title-map-navigation-v1",
                    ),
                    build,
                )
        for version, sha in (
            (CK3_11906.game_version, CK3_12002.executable_sha256),
            (CK3_12002.game_version, CK3_11906.executable_sha256),
            ("1.20.0.3", CK3_12002.executable_sha256),
            (CK3_12002.game_version, "A" * 64),
        ):
            with self.subTest(version=version, sha=sha):
                with self.assertRaises(ValueError):
                    require_exact_native_build(version, sha)

    def test_title_wire_preserves_gameplay_fields_for_both_builds(self):
        for build in (CK3_11906, CK3_12002):
            with self.subTest(version=build.game_version):
                frame = _title_result(build)
                normalized = normalize_native_title_map_navigation_v1_result(
                    frame,
                    expected_title_key="c_bianzhou",
                    expected_snapshot_id=f"native:{title_fixture.NATIVE_REVISION}",
                    expected_native_revision=title_fixture.NATIVE_REVISION,
                    expected_date_raw=title_fixture.DATE_RAW,
                )
                for field in ("source", "title", "camera_center", "binding"):
                    self.assertEqual(normalized[field], frame[field])
                self.assertTrue(normalized["camera_center"]["postcondition_verified"])

    def test_title_wire_rejects_mixed_source_identity(self):
        frame = _title_result(CK3_12002)
        for field, wrong in (
            ("executable_sha256", CK3_11906.executable_sha256),
            ("backend_id", CK3_11906.backend_id("title-map-navigation-v1")),
        ):
            changed = copy.deepcopy(frame)
            changed["source"][field] = wrong
            with self.subTest(field=field), self.assertRaises(ValueError):
                normalize_native_title_map_navigation_v1_result(
                    changed,
                    expected_title_key="c_bianzhou",
                    expected_snapshot_id=f"native:{title_fixture.NATIVE_REVISION}",
                    expected_native_revision=title_fixture.NATIVE_REVISION,
                    expected_date_raw=title_fixture.DATE_RAW,
                )

    def test_native_title_driver_accepts_new_hello_and_result(self):
        driver, endpoint = _driver(CK3_12002)
        title_fixture._answer_with(endpoint, lambda: _title_result(CK3_12002))
        result = driver.center_map_on_landed_title_v1(
            "c_bianzhou", expected_revision=driver.take_snapshot()["revision"],
        )
        self.assertEqual(result["source"], _title_source(CK3_12002))
        self.assertEqual(
            title_fixture._execute_frames(endpoint)[0]["title_key"], "c_bianzhou",
        )

    def test_native_title_driver_rejects_valid_other_build_result(self):
        driver, endpoint = _driver(CK3_12002)
        title_fixture._answer_with(endpoint, lambda: _title_result(CK3_11906))
        with self.assertRaisesRegex(BridgeUnavailableError, "build mirror"):
            driver.center_map_on_landed_title_v1(
                "c_bianzhou", expected_revision=driver.take_snapshot()["revision"],
            )

    def test_service_title_command_accepts_new_and_checks_hello_mirror(self):
        service = GameplayBridgeService(_TitleServiceDriver(CK3_12002, CK3_12002))
        result = service.center_map_on_landed_title_v1(
            "c_bianzhou", expected_revision=title_fixture.PUBLIC_REVISION,
        )
        self.assertEqual(result["source"], _title_source(CK3_12002))
        mismatched = GameplayBridgeService(
            _TitleServiceDriver(CK3_12002, CK3_11906),
        )
        with self.assertRaisesRegex(BridgeUnavailableError, "build mirror"):
            mismatched.center_map_on_landed_title_v1(
                "c_bianzhou", expected_revision=title_fixture.PUBLIC_REVISION,
            )

    def test_war_entry_new_build_uses_its_own_native_provenance(self):
        frame = war_entry_fixture._payload()
        frame["provenance"] = {
            "game_version": "1.20.0.2",
            "executable_sha256": CK3_12002.executable_sha256,
            "assessment_rva": "0x1A23240",
            "network_collector_rva": "0x1A24010",
            "power_leaf": "CCharacter+0x1C0->+0x308",
            "fixed_point_scale": 100_000,
        }
        normalized = normalize_war_entry_assessments(
            frame, expected_target_character_ids=[808],
            expected_actor_character_id=29_829, expected_snapshot_revision=17,
        )
        self.assertEqual(normalized, frame)
        changed = copy.deepcopy(frame)
        changed["provenance"]["power_leaf"] = "CCharacter+0x1B8->+0x308"
        with self.assertRaisesRegex(ValueError, "provenance"):
            normalize_war_entry_assessments(
                changed, expected_target_character_ids=[808],
                expected_actor_character_id=29_829, expected_snapshot_revision=17,
            )

    def test_pending_context_preserves_values_and_requires_new_locators(self):
        frame = pending_fixture._frame()
        frame["build"] = {
            "version": CK3_12002.game_version,
            "exe_sha256": CK3_12002.executable_sha256,
        }
        frame["provenance"] = {
            "backend_id": CK3_12002.backend_id("pending-character-interaction-context-v1"),
            "pending_storage_slot_rva": "0x5D1EC80",
            "character_storage_slot_rva": "0x5C67568",
            "expiration_days_rva": "0x5C68CFC",
            "local_routing_predicate_rva": "0x136D1B0",
            "reply_validator_rva": "0x2968490",
            "auto_accept_trigger_evaluator_rva": "0x372DF30",
            "cost_evaluator_rva": "0x310CEE0",
            "common_war_relation_rva": "0x28BC270",
            "target_type_registry_getter_rva": "0x3795A80",
            "target_type_registry_rva": "0x54F2AF0",
            "script_identifier_name_rva": "0x3F4F900",
            "reply_primary_vtable_rva": "0x448BC18",
            "reply_secondary_vtable_rva": "0x448BBE8",
            "war_victory_special_vtable_rva": "0x46C3AA0",
            "war_white_peace_special_vtable_rva": "0x46C3B10",
            "war_defeat_special_vtable_rva": "0x46C3B80",
        }
        kwargs = {
            "expected_pending_interaction_id": pending_fixture.PENDING_ID,
            "expected_date_raw": pending_fixture.DATE_RAW,
            "expected_snapshot_revision": pending_fixture.NATIVE_REVISION,
        }
        normalized = normalize_pending_character_interaction_context_v1(frame, **kwargs)
        self.assertEqual(normalized, frame)
        self.assertFalse(normalized["readiness"]["interaction_semantic_decision_ready"])
        for section, field, wrong in (
            ("build", "exe_sha256", CK3_11906.executable_sha256),
            ("provenance", "backend_id", CK3_11906.backend_id("pending-character-interaction-context-v1")),
            ("provenance", "pending_storage_slot_rva", "0x57BF1C8"),
        ):
            changed = copy.deepcopy(frame)
            changed[section][field] = wrong
            with self.subTest(field=field), self.assertRaises(ValueError):
                normalize_pending_character_interaction_context_v1(changed, **kwargs)

    def test_event_window_binds_indicator_coverage_to_its_native_locator(self):
        frame = _new_event_frame()
        frame["provenance"] = {
            "root": "module+0x5C6A520->+0x10",
            "idler_vtable_rva": "0x44BC408",
            "manager_offset": "+0x28",
            "backend_id": CK3_12002.backend_id("event-window-v1"),
        }
        frame["options"][0]["effect_indicators"]["coverage"] = (
            "played-character-event-icon-indicators-1.20.0.2-v1"
        )
        kwargs = {
            "expected_event_instance_id": EVENT_INSTANCE_ID,
            "expected_date_raw": EVENT_DATE_RAW,
            "expected_snapshot_revision": EVENT_NATIVE_REVISION,
        }
        self.assertEqual(normalize_current_event_window_context_v1(frame, **kwargs), frame)
        for section, field, wrong in (
            ("provenance", "idler_vtable_rva", "0x44D6048"),
            ("provenance", "backend_id", CK3_11906.backend_id("event-window-v1")),
        ):
            changed = copy.deepcopy(frame)
            changed[section][field] = wrong
            with self.subTest(field=field), self.assertRaises(ValueError):
                normalize_current_event_window_context_v1(changed, **kwargs)
        changed = copy.deepcopy(frame)
        changed["options"][0]["effect_indicators"]["coverage"] = (
            "played-character-event-icon-indicators-1.19.0.6-v1"
        )
        with self.assertRaises(ValueError):
            normalize_current_event_window_context_v1(changed, **kwargs)

    def test_prewar_research_payload_retains_partial_readiness_after_migration(self):
        frame = prewar_fixture._payload()
        frame["provenance"].update(
            game_version=CK3_12002.game_version,
            executable_sha256=CK3_12002.executable_sha256,
            unit_storage_slot_rva="0x5D1E380",
        )
        kwargs = {
            "expected_declaration_id": "29097-11-0",
            "expected_actor_character_id": 29_829,
            "expected_snapshot_revision": 74,
        }
        self.assertEqual(normalize_prewar_primary_scope(frame, **kwargs), frame)
        self.assertFalse(PREWAR_SCOPE_V1_ADVERTISED)
        self.assertFalse(frame["readiness"]["war_entry_forecast_inputs_ready"])
        frame["provenance"]["unit_storage_slot_rva"] = "0x570CC80"
        with self.assertRaisesRegex(ValueError, "provenance"):
            normalize_prewar_primary_scope(frame, **kwargs)

    def test_feature_registry_binds_shifted_indexes_to_the_new_build(self):
        frame = feature_fixture._frame()
        frame["build"] = {
            "version": CK3_12002.game_version,
            "exe_sha256": CK3_12002.executable_sha256,
        }
        frame["provenance"] = {
            "feature_root_slot_rva": "0x5CB87F8",
            "feature_bitset_rva": "root+0x2B0",
            "feature_enum_table_rva": "0x47334C0..0x4733570",
            "script_dlc_set_rva": "0x5CC15E0",
            "backend_id": CK3_12002.backend_id("loaded-feature-manifest-v1"),
        }
        old_items = copy.deepcopy(frame["effective_feature_flags"]["items"])
        items = frame["effective_feature_flags"]["items"]
        self.assertEqual(items[36]["key"], "barter_troops")
        del items[36]
        for index, item in enumerate(items):
            item["native_index"] = index
        items.append({
            "native_index": 43,
            "cstring_id": 0x4169,
            "key": "by_god_alone",
            "enabled": True,
        })
        kwargs = {
            "expected_date_raw": feature_fixture.DATE_RAW,
            "expected_snapshot_revision": feature_fixture.NATIVE_REVISION,
        }
        normalized = normalize_loaded_feature_manifest_v1(frame, **kwargs)
        self.assertEqual(normalized, frame)
        self.assertEqual(normalized["effective_feature_flags"]["items"][36]["key"], "high_medieval_warfare_attire")
        self.assertFalse(normalized["readiness"]["entitlements_ready"])
        changed = copy.deepcopy(frame)
        changed["effective_feature_flags"]["items"] = old_items
        with self.assertRaisesRegex(ValueError, "registry"):
            normalize_loaded_feature_manifest_v1(changed, **kwargs)
        changed = copy.deepcopy(frame)
        changed["build"]["exe_sha256"] = CK3_11906.executable_sha256
        with self.assertRaisesRegex(ValueError, "build"):
            normalize_loaded_feature_manifest_v1(changed, **kwargs)

    def test_claim_terms_uses_new_claim_reader_and_new_script_fingerprint(self):
        frame = terms_fixture._available_terms()
        frame["provenance"] = {
            "game_version": CK3_12002.game_version,
            "executable_sha256": CK3_12002.executable_sha256,
            "native_reader": "CWar+0x270/+0x290;0x2B9ECD0",
            "present_claim_lifecycle": "present_only_vtable_slot_0_delete_flags_0",
            "claim_script_sha256": "887BF0197401CB17CB4588978ADD556AB6B429BF55CB482E3E5F2D0E8351CFD4",
        }
        self.assertEqual(
            normalize_war_termination_terms(frame, expected_war_id=terms_fixture.WAR_ID),
            frame,
        )
        for field, wrong in (
            ("native_reader", "CWar+0x270/+0x290;0x28B1AA0"),
            ("claim_script_sha256", terms_fixture._provenance()["claim_script_sha256"]),
        ):
            changed = copy.deepcopy(frame)
            changed["provenance"][field] = wrong
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "provenance"):
                normalize_war_termination_terms(changed, expected_war_id=terms_fixture.WAR_ID)

    def test_campaign_root_requires_new_getter_provenance_without_changing_semantics(self):
        frame = campaign_fixture._frame()
        frame["provenance"] = {
            "game_version": CK3_12002.game_version,
            "executable_sha256": CK3_12002.executable_sha256,
            "backend_id": CK3_12002.backend_id("campaign-root-context-v1"),
            "primary_title_rva": "0x289DA30",
            "capital_province_rva": "0x28B1CD0",
            "immediate_liege_rva": "0x28BFC70",
            "top_liege_rva": "0x28BFDA0",
            "government_rva": "0x28C2E10",
            "selected_game_rule_service_slot_rva": "0x5CB3D78",
        }
        kwargs = {
            "expected_date_raw": campaign_fixture.DATE_RAW,
            "expected_snapshot_revision": campaign_fixture.NATIVE_REVISION,
        }
        normalized = normalize_campaign_root_context_v1(frame, **kwargs)
        self.assertEqual(normalized, frame)
        self.assertEqual(normalized["government"]["flags"].count("government_is_settled"), 2)
        changed = copy.deepcopy(frame)
        changed["provenance"]["executable_sha256"] = CK3_11906.executable_sha256
        with self.assertRaisesRegex(ValueError, "provenance"):
            normalize_campaign_root_context_v1(changed, **kwargs)
        changed = copy.deepcopy(frame)
        changed["provenance"]["primary_title_rva"] = "0x25F3350"
        with self.assertRaisesRegex(ValueError, "provenance"):
            normalize_campaign_root_context_v1(changed, **kwargs)

    def test_compiled_native_pending_reader_wire_is_accepted_directly(self):
        fixture = PROJECT_ROOT / "tests/fixtures/ck3_12002_pending_context_native.json"
        frame = json.loads(fixture.read_text(encoding="utf-8-sig"))
        normalized = normalize_pending_character_interaction_context_v1(
            frame, expected_pending_interaction_id=16_777_249,
            expected_date_raw=53_175_816, expected_snapshot_revision=47,
        )
        self.assertEqual(normalized, frame)
        self.assertEqual(normalized["roles"]["recipient_character_id"], 2001)
        self.assertEqual(normalized["deadline"]["remaining_days"], 43)
        self.assertEqual(normalized["terms"]["structured_costs"]["value"]["entries"][9], {
            "resource_key": "barter_goods", "raw": 400_000,
        })

    def test_new_event_indicator_kinds_preserve_both_materialized_directions(self):
        frame = _new_event_frame()
        frame["provenance"] = {
            "root": "module+0x5C6A520->+0x10",
            "idler_vtable_rva": "0x44BC408",
            "manager_offset": "+0x28",
            "backend_id": CK3_12002.backend_id("event-window-v1"),
        }
        indicators = frame["options"][0]["effect_indicators"]
        indicators["coverage"] = "played-character-event-icon-indicators-1.20.0.2-v1"
        fulfillment = {
            "kind": "fulfillment", "direction": "increase",
            "magnitude": {"status": "unavailable"},
            "affected_by_trait": False, "critical": False,
        }
        combined = {
            "kind": "stress_and_fulfillment", "direction": "decrease",
            "secondary_direction": "increase",
            "magnitude": {"status": "unavailable"},
            "affected_by_trait": True, "critical": True,
        }
        indicators["rows"] = [fulfillment, combined]
        kwargs = {
            "expected_event_instance_id": EVENT_INSTANCE_ID,
            "expected_date_raw": EVENT_DATE_RAW,
            "expected_snapshot_revision": EVENT_NATIVE_REVISION,
        }
        normalized = normalize_current_event_window_context_v1(frame, **kwargs)
        self.assertEqual(normalized["options"][0]["effect_indicators"]["rows"], [fulfillment, combined])
        self.assertFalse(normalized["readiness"]["semantic_decision_ready"])
        changed = copy.deepcopy(frame)
        changed["options"][0]["effect_indicators"]["rows"][1]["secondary_direction"] = "not_applicable"
        with self.assertRaisesRegex(ValueError, "secondary_direction"):
            normalize_current_event_window_context_v1(changed, **kwargs)
        changed = copy.deepcopy(frame)
        changed["options"][0]["effect_indicators"]["rows"] = [{"kind": "unknown", "raw_kind": 4}]
        with self.assertRaisesRegex(ValueError, "known kind"):
            normalize_current_event_window_context_v1(changed, **kwargs)
        changed = copy.deepcopy(frame)
        changed["provenance"] = _old_event_provenance()
        changed["options"][0]["effect_indicators"]["coverage"] = (
            "played-character-event-icon-indicators-1.19.0.6-v1"
        )
        with self.assertRaisesRegex(ValueError, "exact build"):
            normalize_current_event_window_context_v1(changed, **kwargs)

    def test_compiled_native_event_reader_wire_keeps_new_indicator_directions(self):
        fixture = PROJECT_ROOT / "tests/fixtures/ck3_12002_event_window_native.json"
        frame = json.loads(fixture.read_text(encoding="utf-8-sig"))
        normalized = normalize_current_event_window_context_v1(
            frame, expected_event_instance_id=16_777_257,
            expected_date_raw=frame["date_raw"], expected_snapshot_revision=17,
        )
        self.assertEqual(normalized, frame)
        rows = [
            row for option in normalized["options"]
            for row in option["effect_indicators"]["rows"]
        ]
        fulfillment = next(row for row in rows if row["kind"] == "fulfillment")
        combined = next(row for row in rows if row["kind"] == "stress_and_fulfillment")
        self.assertEqual(fulfillment["direction"], "increase")
        self.assertEqual((combined["direction"], combined["secondary_direction"]), ("increase", "decrease"))
        self.assertTrue(combined["affected_by_trait"])
        self.assertTrue(combined["critical"])

    def test_committed_old_event_wire_retains_null_scope_schema(self):
        fixture = PROJECT_ROOT / "tests/fixtures/ck3_11906_event_window_legacy.json"
        frame = json.loads(fixture.read_text(encoding="utf-8-sig"))
        kwargs = {
            "expected_event_instance_id": EVENT_INSTANCE_ID,
            "expected_date_raw": EVENT_DATE_RAW,
            "expected_snapshot_revision": EVENT_NATIVE_REVISION,
        }
        self.assertEqual(normalize_current_event_window_context_v1(frame, **kwargs), frame)
        self.assertNotIn("root_scope_ready", frame["readiness"])
        self.assertIsNone(frame["root_scope"])
        changed = copy.deepcopy(frame)
        changed["provenance"] = _new_event_frame()["provenance"]
        with self.assertRaisesRegex(ValueError, "readiness"):
            normalize_current_event_window_context_v1(changed, **kwargs)


if __name__ == "__main__":
    unittest.main()
