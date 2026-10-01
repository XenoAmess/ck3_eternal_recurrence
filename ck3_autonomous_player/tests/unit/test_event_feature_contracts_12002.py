"""Offline wire compatibility for 1.20 while retaining master 1.19 semantics."""

from __future__ import annotations

import copy
import unittest

from ck3_autonomous_player.tests.unit import test_event_window_context_v1_bridge as events
from ck3_autonomous_player.tests.unit import test_loaded_feature_manifest_v1_bridge as features
from ck3_autonomous_player.tests.unit import test_pending_character_interaction_context_v1_bridge as pending

from xar_autoplayer.bridge.event_window_context_contract import (
    normalize_current_event_window_context_v1,
)
from xar_autoplayer.bridge.loaded_feature_manifest_contract import (
    normalize_loaded_feature_manifest_v1,
)
from xar_autoplayer.bridge.pending_character_interaction_context_contract import (
    normalize_pending_character_interaction_context_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


EVENT_PROVENANCE = {
    "root": "module+0x5C6A520->+0x10",
    "idler_vtable_rva": "0x44BC408",
    "manager_offset": "+0x28",
    "backend_id": "ck3-1.20.0.2-native-event-window-v1",
}
PENDING_PROVENANCE = {
    "backend_id": "ck3-1.20.0.2-native-pending-character-interaction-context-v1",
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
FEATURE_PROVENANCE = {
    "feature_root_slot_rva": "0x5CB87F8",
    "feature_bitset_rva": "root+0x2B0",
    "feature_enum_table_rva": "0x47334C0..0x4733570",
    "script_dlc_set_rva": "0x5CC15E0",
    "backend_id": "ck3-1.20.0.2-native-loaded-feature-manifest-v1",
}


def _build() -> dict[str, str]:
    return {
        "version": CK3_12002.game_version,
        "exe_sha256": CK3_12002.executable_sha256,
    }


def _event_frame(status: str = "available") -> dict[str, object]:
    frame = events._frame(status)
    frame["provenance"] = dict(EVENT_PROVENANCE)
    if status == "available":
        for option in frame["options"]:
            option["effect_indicators"]["coverage"] = (
                "played-character-event-icon-indicators-1.20.0.2-v1"
            )
    return frame


def _pending_frame(status: str = "available", **kwargs) -> dict[str, object]:
    frame = pending._frame(status, **kwargs)
    frame["build"] = _build()
    frame["provenance"] = dict(PENDING_PROVENANCE)
    return frame


def _feature_frame(status: str = "available") -> dict[str, object]:
    frame = features._frame(status)
    frame["build"] = _build()
    frame["provenance"] = dict(FEATURE_PROVENANCE)
    if status == "available":
        items = frame["effective_feature_flags"]["items"]
        items.pop(36)  # barter_troops removed from the 1.20 native enum.
        items.append({
            "native_index": 43,
            "cstring_id": 0x4169,
            "key": "by_god_alone",
            "enabled": False,
        })
        for index, item in enumerate(items):
            item["native_index"] = index
    return frame


def _event(frame):
    return normalize_current_event_window_context_v1(
        frame,
        expected_event_instance_id=events.EVENT_ID,
        expected_date_raw=events.DATE_RAW,
        expected_snapshot_revision=events.NATIVE_REVISION,
    )


def _pending(frame):
    return normalize_pending_character_interaction_context_v1(
        frame,
        expected_pending_interaction_id=frame["pending_interaction_id"],
        expected_date_raw=pending.DATE_RAW,
        expected_snapshot_revision=pending.NATIVE_REVISION,
    )


def _features(frame):
    return normalize_loaded_feature_manifest_v1(
        frame,
        expected_date_raw=features.DATE_RAW,
        expected_snapshot_revision=features.NATIVE_REVISION,
    )


class EventFeatureContract12002Tests(unittest.TestCase):
    def test_event_new_build_preserves_scope_inventory_and_stale_saved_character(self):
        frame = _event_frame()
        frame["saved_scopes"][0]["scope"]["typed_identity"] = {
            "status": "unavailable",
            "reason": "character_scope_identity_unavailable",
        }
        normalized = _event(frame)
        self.assertEqual(normalized, frame)
        normalized["saved_scopes"].clear()
        self.assertEqual(len(frame["saved_scopes"]), 2)

    def test_event_new_fulfillment_and_combined_stress_indicators(self):
        frame = _event_frame()
        rows = frame["options"][0]["effect_indicators"]["rows"]
        rows.extend([
            {
                "kind": "fulfillment", "direction": "increase",
                "magnitude": {"status": "unavailable"},
                "affected_by_trait": False, "critical": False,
            },
            {
                "kind": "stress_and_fulfillment", "direction": "decrease",
                "secondary_direction": "increase",
                "magnitude": {"status": "unavailable"},
                "affected_by_trait": True, "critical": True,
            },
        ])
        normalized = _event(frame)
        self.assertEqual(normalized["options"][0]["effect_indicators"]["rows"], rows)
        self.assertFalse(normalized["readiness"]["effect_preview_ready"])
        self.assertFalse(normalized["readiness"]["semantic_decision_ready"])

    def test_indicator_enum_expansion_is_version_specific(self):
        old = events._frame()
        old["options"][0]["effect_indicators"]["rows"] = [{"kind": "unknown", "raw_kind": 4}]
        self.assertEqual(_event(old), old)
        new = _event_frame()
        new["options"][0]["effect_indicators"]["rows"] = [{"kind": "unknown", "raw_kind": 4}]
        with self.assertRaisesRegex(ValueError, "known kind"):
            _event(new)
        old["options"][0]["effect_indicators"]["rows"] = [{
            "kind": "fulfillment", "direction": "increase",
            "magnitude": {"status": "unavailable"},
            "affected_by_trait": False, "critical": False,
        }]
        with self.assertRaisesRegex(ValueError, "exact build"):
            _event(old)

    def test_event_uses_matching_provenance_and_indicator_coverage(self):
        frame = _event_frame()
        frame["provenance"]["idler_vtable_rva"] = "0x40B1D30"
        with self.assertRaisesRegex(ValueError, "locator drifted"):
            _event(frame)
        frame = _event_frame()
        frame["options"][0]["effect_indicators"]["coverage"] = (
            "played-character-event-icon-indicators-1.19.0.6-v1"
        )
        with self.assertRaisesRegex(ValueError, "indicators are invalid"):
            _event(frame)

    def test_event_new_unavailable_frame_keeps_null_scopes(self):
        frame = _event_frame("unavailable")
        self.assertEqual(_event(frame), frame)

    def test_pending_new_build_preserves_signed_full_generation_identity(self):
        frame = _pending_frame()
        frame["pending_interaction_id"] = -(2**31) + 93
        normalized = _pending(frame)
        self.assertEqual(normalized["pending_interaction_id"], -(2**31) + 93)
        self.assertEqual(normalized["provenance"], PENDING_PROVENANCE)

    def test_pending_new_build_preserves_call_ally_typed_war_target(self):
        frame = _pending_frame(definition_key="call_ally_interaction", target_war=True)
        normalized = _pending(frame)
        self.assertEqual(normalized["target"]["typed_identity"], "war:67108946")
        self.assertTrue(normalized["readiness"]["target_typed_identity_ready"])

    def test_pending_new_build_preserves_special_war_binding(self):
        frame = _pending_frame(
            special_war_binding=pending._white_peace_binding(),
            definition_key="end_war_attacker_white_peace_interaction",
        )
        normalized = _pending(frame)
        self.assertEqual(normalized["terms"]["special_war_binding"]["value"]["absolute_outcome"], "white_peace")
        self.assertTrue(normalized["readiness"]["special_war_binding_ready"])

    def test_pending_new_unavailable_and_invalid_frames(self):
        for status in ("unavailable", "invalid"):
            with self.subTest(status=status):
                frame = _pending_frame(status)
                normalized = _pending(frame)
                self.assertEqual(normalized["status"], status)
                self.assertFalse(normalized["readiness"]["same_frame_ready"])

    def test_features_new_build_uses_new_native_enum_without_claiming_entitlements(self):
        normalized = _features(_feature_frame())
        items = normalized["effective_feature_flags"]["items"]
        self.assertEqual(len(items), 44)
        self.assertNotIn("barter_troops", {item["key"] for item in items})
        self.assertEqual(items[43]["key"], "by_god_alone")
        self.assertFalse(normalized["readiness"]["entitlements_ready"])

    def test_features_new_unavailable_frame(self):
        frame = _feature_frame("unavailable")
        self.assertEqual(_features(frame), frame)

    def test_new_build_frames_cannot_use_old_sha_or_locators(self):
        for factory, normalize, old_fixture in (
            (_pending_frame, _pending, pending._frame),
            (_feature_frame, _features, features._frame),
        ):
            with self.subTest(factory=factory.__name__):
                frame = factory()
                frame["build"]["exe_sha256"] = old_fixture()["build"]["exe_sha256"]
                with self.assertRaisesRegex(ValueError, "frozen exact build"):
                    normalize(frame)
                frame = factory()
                frame["provenance"] = copy.deepcopy(old_fixture()["provenance"])
                with self.assertRaisesRegex(ValueError, "provenance"):
                    normalize(frame)


if __name__ == "__main__":
    unittest.main()
