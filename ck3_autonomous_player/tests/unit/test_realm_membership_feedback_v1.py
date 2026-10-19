"""Synthetic portable contracts; no runtime files, Native calls or SAVE reads."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge.player_faction_alerts_contract import (
    SUBREALM_COUNTIES_COMPONENT_V1 as COMPONENT,
    SUBREALM_COUNTIES_SCOPE_V1 as SCOPE,
    SUBREALM_COUNTIES_SOURCE_V1 as SOURCE,
    normalize_player_faction_alerts_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.campaign_score_existing_inputs_v1 import project_existing_month_inputs_v1
from xar_autoplayer.realm_membership_feedback_v1 import project_realm_membership_feedback_v1 as project


def inputs(ids=(2231, 2262, 2488), *, native=41, public=9, date=53144328, query=1):
    frame = {"schema": "xar.ck3.planning-source-frame/v1", "status": "complete",
        "snapshot_id": f"native:{native}", "revision": public, "native_revision": native,
        "date_raw": date, "actor_character_id": 31254,
        "episode_run_id": "native-31254-synthetic", "bridge_pid": 44, "connection_generation": 3}
    snapshot = {k: frame[k] for k in ("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")}
    snapshot.update(paused=True, map_ready=True, played_character={"character_id": 31254, "alive": True},
        diagnostics={"bridge_pid": 44, "connection_generation": 3,
            "hello": {"game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256}})
    material = {"schema_version": 1, "status": "available", "snapshot_revision": native,
        "date_raw": date, "player_character_id": 31254, "targeting_faction_count": 0,
        "targeting_factions": [], "county_exposures": [],
        "planner_projection": {"status": "available", "present": False, "dangerous": False,
            "dangerous_faction_ids": [], "watch_faction_ids": [], "war_handoff_faction_ids": [],
            "exposed_county_title_ids": [], "exact_ultimatum_timing_ready": False},
        "readiness": {k: k != "exact_ultimatum_timing_ready" for k in (
            "identity_ready", "targeting_count_ready", "targeting_rows_ready", "county_exposure_ready",
            "stock_dangerous_predicate_ready", "same_frame_ready", "alert_ready", "exact_ultimatum_timing_ready")},
        "component_unavailable_reasons": {"targeting_rows": None, "county_exposure": None},
        "unavailable_reason": None,
        "provenance": {"game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
            "backend_id": CK3_12004.backend_id("player-faction-alerts-v1")},
        COMPONENT: {"status": "available", "complete": True, "scope": SCOPE, "source": SOURCE,
            "snapshot_revision": native, "date_raw": date, "actor_character_id": 31254,
            "county_title_ids": list(ids), "unavailable_reason": None}}
    packet = {"query_sequence": query, "player_faction_alerts": material,
        "binding": {**{k: frame[k] for k in ("snapshot_id", "revision", "native_revision", "date_raw")},
                    "expected_revision": public}}
    return snapshot, frame, packet


def observe(args, previous=None):
    snapshot, frame, packet = args
    return project(snapshot, faction_result=packet, source_frame=frame, previous=previous)


class RealmMembershipFeedbackTests(unittest.TestCase):
    def test_optional_absence_keeps_original_alerts_and_unknown_count(self):
        args = inputs(); packet = args[2]; del packet["player_faction_alerts"][COMPONENT]
        old = deepcopy(packet["player_faction_alerts"])
        self.assertEqual(normalize_player_faction_alerts_v1(old, expected_date_raw=53144328,
            expected_snapshot_revision=41), old)
        result = observe(args)
        self.assertIsNone(result["raw_metrics"]["realm_county_count"]["value"])
        self.assertIsNone(result["observation"])

    def test_zero_factions_publish_full_realm_and_loss_includes_vassal_county(self):
        first = inputs(); original = deepcopy(first)
        before = observe(first)["observation"]
        result = observe(inputs((2231, 2262), native=42, public=10, date=53144352, query=2), before)
        self.assertEqual(result["raw_metrics"]["realm_county_count"]["value"], "2")
        self.assertEqual(result["difference"]["lost_county_title_ids"], [2488])
        self.assertEqual(result["difference"]["gained_county_title_ids"], [])
        self.assertEqual(first, original)
        self.assertFalse(result["same_native_capture_with_MET"])
        self.assertEqual(result["new_RPC_calls"], 0)

    def test_native_owner_date_revision_and_partial_vector_are_rejected(self):
        for key, value in (("actor_character_id", 7), ("snapshot_revision", 40),
                           ("date_raw", 53144304), ("scope", "top_liege_realm"),
                           ("source", "camera"), ("county_title_ids", [2262, 2231])):
            with self.subTest(key=key):
                args = inputs(); args[2]["player_faction_alerts"][COMPONENT][key] = value
                result = observe(args)
                self.assertEqual(result["status"], "unavailable")
                self.assertIsNone(result["raw_metrics"]["realm_county_count"]["value"])
        args = inputs(); component = args[2]["player_faction_alerts"][COMPONENT]
        component.update(status="unavailable", complete=False, unavailable_reason="native_membership_unavailable")
        self.assertEqual(observe(args)["status"], "unavailable")  # partial list still present
        component["county_title_ids"] = None
        self.assertEqual(observe(args)["status"], "unavailable")

    def test_old_auto_frame_never_becomes_current_month(self):
        for location, key in ((0, "native_revision"), (0, "date_raw"), (0, "revision"),
                              (1, "actor_character_id")):
            with self.subTest(key=key):
                args = inputs(); args[location][key] += 1
                result = observe(args)
                self.assertIsNone(result["observation"])
                self.assertIsNone(result["raw_metrics"]["realm_county_count"]["value"])
        args = inputs(); args[2]["binding"]["native_revision"] -= 1
        self.assertEqual(observe(args)["status"], "unavailable")

    def test_repeat_incomplete_or_new_owner_previous_never_means_zero_loss(self):
        args = inputs(); previous = observe(args)["observation"]
        self.assertIsNone(observe(args, previous)["difference"]["lost_county_title_ids"])
        for mutate in ("incomplete", "generation", "episode", "missing_frame", "negative_revision"):
            old = deepcopy(previous)
            if mutate == "incomplete":
                old["component"].update(status="unavailable", complete=False,
                    county_title_ids=None, unavailable_reason="source_missing")
            elif mutate == "generation": old["source_frame"]["connection_generation"] += 1
            elif mutate == "episode": old["source_frame"]["episode_run_id"] = "other"
            elif mutate == "missing_frame": del old["source_frame"]["snapshot_id"]
            else: old["source_frame"]["revision"] = -1
            current = observe(inputs(native=42, public=10, query=2), old)
            self.assertEqual(current["status"], "available")
            self.assertEqual(current["difference"]["status"], "unavailable")

    def test_only_complete_successful_empty_collection_is_zero(self):
        result = observe(inputs(()))
        self.assertEqual(result["raw_metrics"]["realm_county_count"]["value"], "0")
        self.assertEqual(result["observation"]["component"]["county_title_ids"], [])
        missing = project(inputs()[0])
        self.assertIsNone(missing["raw_metrics"]["realm_county_count"]["value"])

    def test_full_generation_ids_are_not_compared_by_storage_index(self):
        old = observe(inputs((16777227, 16777228)))["observation"]
        new = observe(inputs((11, 16777228), native=42, public=10, query=2), old)
        self.assertEqual(new["difference"]["lost_county_title_ids"], [16777227])
        self.assertEqual(new["difference"]["gained_county_title_ids"], [11])

    def test_invalid_build_or_missing_original_query_is_unknown(self):
        args = inputs(); args[0]["diagnostics"]["hello"]["game_version"] = "unknown"
        self.assertEqual(observe(args)["status"], "unavailable")

    def test_ordinary_native_driver_DTO_is_used_without_inventing_service_binding(self):
        args = inputs(); frame, packet = args[1:]
        del packet["binding"]
        packet.update(step="query-player-faction-alerts-v1", accepted=True, status="available",
            snapshot_revision=frame["native_revision"], player_faction_alerts_ready=True,
            queried_snapshot_id=frame["snapshot_id"], queried_revision=frame["revision"],
            queried_native_revision=frame["native_revision"])
        self.assertEqual(observe(args)["status"], "available")
        packet["queried_revision"] -= 1
        self.assertIsNone(observe(args)["raw_metrics"]["realm_county_count"]["value"])
        args = inputs(); del args[2]["query_sequence"]
        self.assertEqual(observe(args)["status"], "unavailable")

    def test_optional_month_mapping_adds_no_query_and_stale_frame_stays_unknown(self):
        snap, frame, packet = inputs()
        old = project_existing_month_inputs_v1(snap)
        self.assertNotIn("realm_county_count", old["raw_metrics"])
        result = project_existing_month_inputs_v1(snap, faction_result=packet, faction_source_frame=frame)
        self.assertEqual(result["raw_metrics"]["realm_county_count"]["value"], "3")
        self.assertEqual(result["sources"][0]["binding"], frame)
        snap["native_revision"] += 1
        stale = project_existing_month_inputs_v1(snap, faction_result=packet, faction_source_frame=frame)
        self.assertIsNone(stale["raw_metrics"]["realm_county_count"]["value"])
        self.assertEqual(stale["new_RPC_calls"], 0)


if __name__ == "__main__":
    unittest.main()
