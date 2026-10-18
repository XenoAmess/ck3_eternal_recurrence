"""Synthetic post-Continue observations; no Game, Native or owner adoption."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.succession_ui_observation_v1 import project_successor_ui_observation_v1 as project
from xar_autoplayer.bridge.version_identity import CK3_12004


def material():
    # Deliberately unrelated to actual IDs, dates or process identity.
    snapshot = {
        "snapshot_id": "synthetic:17", "revision": 21, "native_revision": 17,
        "date_raw": 53000000, "paused": True, "map_ready": True,
        "played_character": {"character_id": 23, "alive": True},
        "episode_run_id": "synthetic-successor", "episode_character_id": 23,
        "episode_identity_pending": False, "one_life_terminal_reason": None,
        "active_event": {"instance_id": 47},
        "diagnostics": {"bridge_pid": 123, "connection_generation": 2, "hello": {
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256}},
    }
    available = lambda value: {"status": "available", "value": value, "unavailable_reason": None}
    timeline = {
        "schema": "current-timeline-blocker-context-v1", "schema_version": 1,
        "status": "available", "snapshot_revision": 17, "date_raw": snapshot["date_raw"],
        "identity": "none", "blocks_simulation": available(True),
        "has_open_succession": available(True),
        "can_continue": {"status": "unavailable", "value": None,
                         "unavailable_reason": "no_supported_timeline_surface_visible"},
        "evidence_source": {"kind": "exact-build-stock-gui-plus-native-widget-state",
                            "path": "game/gui/window_succession_event.gui",
                            "root_name": "none", "decisive_widget_name": "none"},
        "unavailable_reason": None,
    }
    event = {
        "schema": "current-event-window-context-v1", "schema_version": 1,
        "status": "available", "snapshot_revision": 17, "date_raw": snapshot["date_raw"],
        "current_event_instance_id": 47, "window_match_count": 1,
        "unavailable_reason": None, "event_definition_key": "synthetic_succession.0001",
        "calculated_event_id": 12345, "runtime_stats_ordinal": 31,
        "root_scope": {"status": "available", "raw_type_index": 4, "type_key": "character", "subtype": 0,
                       "typed_identity": {"status": "available", "kind": "character", "character_id": 19}},
        "saved_scopes": [], "options": [{
            "rendered_index": 0, "native_option_index": 0, "shown": True, "enabled": True,
            "fallback": False, "cancel": False, "resolved_name": "Synthetic continue",
            "unavailable_reason": "", "effect_indicators": {"status": "available",
                "coverage": "played-character-event-icon-indicators-1.20.0.4-v1",
                "complete_effect_set": False, "rows": []},
            "effect_preview": {"status": "unavailable", "reason": "indicator_subset_has_no_completeness_signal"},
            "resource_deltas": {"status": "unavailable"}, "relationship_deltas": {"status": "unavailable"}}],
        "readiness": {"event_definition_identity_ready": True, "root_scope_ready": True,
            "saved_scopes_ready": True, "option_presentation_ready": True, "effect_indicators_ready": True,
            "effect_preview_ready": False, "semantic_decision_ready": False},
        "provenance": {"root": "module+0x5C6A520->+0x10", "idler_vtable_rva": "0x44BC418",
                       "manager_offset": "+0x28", "backend_id": CK3_12004.backend_id("event-window-v1")},
    }
    return snapshot, timeline, event


class SuccessionUiObservationTests(unittest.TestCase):
    def test_old_root_event_does_not_clear_succession_or_authorize_actions(self):
        snapshot, timeline, event = material()
        original = deepcopy((snapshot, timeline, event))
        result = project(snapshot, timeline_context=timeline, event_context=event)
        self.assertEqual(result["ui_clearance"], "unresolved")
        self.assertEqual(result["event_root_scope"]["typed_identity"]["character_id"], 19)
        self.assertEqual(result["frame"]["played_character_id"], 23)
        self.assertEqual(result["timeline"], timeline)
        self.assertTrue(result["fresh_timeline_read_after_event_required"])
        self.assertFalse(result["event_semantic_decision_ready"])
        self.assertFalse(result["authorizes_close_or_save"])
        self.assertFalse(result["authorizes_event_selection"])
        self.assertEqual(result["business_cycle_credit"], 0)
        self.assertEqual((snapshot, timeline, event), original)
        result["event_root_scope"]["typed_identity"]["character_id"] = 1
        self.assertEqual(event["root_scope"]["typed_identity"]["character_id"], 19)

    def test_unavailable_event_stays_unknown_without_blocking_original_event_policy(self):
        snapshot, timeline, event = material()
        event.update(status="unavailable", unavailable_reason="event_window_not_materialized",
                     window_match_count=0, event_definition_key=None, calculated_event_id=None,
                     runtime_stats_ordinal=None, root_scope=None, saved_scopes=None, options=None)
        event["readiness"] = dict.fromkeys(event["readiness"], False)
        result = project(snapshot, timeline_context=timeline, event_context=event)
        self.assertEqual(result["ui_clearance"], "unresolved")
        self.assertEqual(result["event_context_status"], "unavailable")
        self.assertIsNone(result["event_root_scope"])
        self.assertTrue(result["ordinary_event_policy_unchanged"])
        self.assertFalse(result["authorizes_event_selection"])

    def test_event_disappearance_alone_is_not_clear_and_all_modal_kinds_remain_explicit(self):
        snapshot, timeline, _ = material()
        snapshot["active_event"] = None
        self.assertEqual(project(snapshot, timeline_context=timeline)["ui_clearance"], "unresolved")
        for identity in ("death_succession_modal", "game_over_modal", "succession_select_destiny_modal"):
            modal = deepcopy(timeline)
            modal["identity"] = identity
            modal["can_continue"] = {"status": "available", "value": identity != "game_over_modal",
                                      "unavailable_reason": None}
            self.assertEqual(project(snapshot, timeline_context=modal)["ui_clearance"], "modal_present")
        timeline["blocks_simulation"]["value"] = False
        self.assertEqual(project(snapshot, timeline_context=timeline)["ui_clearance"], "unresolved")
        timeline["has_open_succession"]["value"] = False
        result = project(snapshot, timeline_context=timeline)
        self.assertEqual(result["ui_clearance"], "clear")
        self.assertFalse(result["authorizes_close_or_save"])
        timeline.update(status="unavailable", unavailable_reason="reader_not_ready")
        for key in ("blocks_simulation", "has_open_succession"):
            timeline[key] = {"status": "unavailable", "value": None, "unavailable_reason": "reader_not_ready"}
        timeline["evidence_source"] = dict.fromkeys(timeline["evidence_source"], "")
        self.assertEqual(project(snapshot, timeline_context=timeline)["ui_clearance"], "unknown")

    def test_original_normalizers_reject_foreign_or_malformed_inputs(self):
        for changed in ("old_timeline", "old_event", "foreign_event", "other_build", "pending_episode",
                        "old_episode_actor", "mixed_actor", "stale_event_after_clear"):
            with self.subTest(changed=changed):
                snapshot, timeline, event = material()
                if changed == "old_timeline": timeline["snapshot_revision"] -= 1
                if changed == "old_event": event["date_raw"] -= 24
                if changed == "foreign_event": event["current_event_instance_id"] += 1
                if changed == "other_build": snapshot["diagnostics"]["hello"]["expected_ck3_sha256"] = "0" * 64
                if changed == "pending_episode": snapshot["episode_identity_pending"] = True
                if changed == "old_episode_actor": snapshot["episode_character_id"] = 19
                if changed == "mixed_actor": snapshot.update(played_character_id=29, episode_character_id=29)
                if changed == "stale_event_after_clear": snapshot["active_event"] = None
                with self.assertRaises((ValueError, RuntimeError)):
                    project(snapshot, timeline_context=timeline, event_context=event)


if __name__ == "__main__":
    unittest.main()
