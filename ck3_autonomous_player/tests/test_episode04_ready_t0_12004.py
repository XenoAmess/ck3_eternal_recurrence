"""New readiness joins; every fixture is synthetic, never new CK3 credit."""
from copy import deepcopy
import unittest

from xar_autoplayer.bridge.episode04_ready_t0_12004 import (
    EXE_12004, evaluate_episode04_ready_t0_12004, ready_t0_readonly_requests_12004,
)


def fixture():
    meta = {"queried_snapshot_id": "native:100", "queried_revision": 101,
            "queried_native_revision": 100}
    army = {"army_id": 18, "owner_character_id": 31254, "source": "native", "controllable": True,
            "current_province_id": 2645, "in_combat": False, "retreating": False,
            "army_state": "regular", "army_state_code": 1,
            "route_province_ids": [], "route_read_status": "complete_empty", "route_source_count": 0}
    frame = {"snapshot_id": "native:100", "revision": 101, "native_revision": 100,
             "date_raw": 53147520, "paused": True, "map_ready": True,
             "episode_run_id": "synthetic-episode", "active_event": None, "pending_character_interaction": None,
             "played_character": {"character_id": 31254, "alive": True},
             "diagnostics": {"bridge_pid": 1234, "connection_generation": 1,
                             "hello": {"expected_ck3_version": "1.20.0.4", "expected_ck3_sha256": EXE_12004}},
             "active_wars": [{"war_id": 4, "player_side": "attacker"}],
             # An unrelated army's battle must not make selected18 ineligible.
             "player_armies": [army, {"army_id": 93, "in_combat": True}]}
    record = {"status": "available", "unavailable_reason": None, "record_index": 0,
              "persistent_regiment_id": 17292, "chunk_index": 0, "chunk_army_regiment_id": 51,
              "current_soldiers": 1183, "maximum_soldiers": 1194, "effective_current_soldiers": 1183,
              "state_raw": 0, "native_can_replenish": True, "native_chunk_can_replenish": True,
              "persistent_monthly_replenishment_fraction_raw": 10000,
              "persistent_prepared_replenishment_fraction_raw": 0,
              "persistent_monthly_replenishment_fraction_scale": 100000,
              "persistent_prepared_replenishment_fraction_scale": 100000}
    def data(identity, records, skipped):
        return {"army_regiment_id": identity, "source": "native_all_data_records", "status": "available",
                "ready": True, "native_data_record_count": len(records), "unavailable_reason": None,
                "records": records, "native_loss_writer_skipped": skipped,
                "loss_writer_admission_unavailable_reason": None}
    row = {"status": "available", "army_id": 18, "native_carmy_id": 18, "scope_role": "player", "war_ids": [4],
           "regiment_count": 2, "current_soldiers": 1184, "maximum_soldiers": 1195,
           "ai_base_power_raw": 100000, "ai_base_power_scale": 100000, "unavailable_reason": None,
           "current_supply_raw": 30000000, "current_supply_scale": 100000,
           "current_supply_capacity_raw": 30000000, "current_supply_capacity_scale": 100000,
           "regiment_strengths": [{"army_regiment_id": 51, "current_soldiers": 1183, "maximum_soldiers": 1194, "scale": 1},
                                  {"army_regiment_id": 55, "current_soldiers": 1, "maximum_soldiers": 1, "scale": 1}],
           "regiment_replenishment_records_v1": [data(51, [record], False), data(55, [], True)]}
    query = {**meta, "accepted": True, "queried_date_raw": frame["date_raw"],
             "army_strengths_profile": "ordinary_core_v1", "army_observed_phase_coverage": "not_requested",
             "army_strengths": [row]}
    commander = {**meta, "accepted": True, "read_only": True,
                 "army_commander_candidates": {"schema": "ck3_12004_army_commander_candidates_v1",
                    "status": "partial", "snapshot_revision": 100, "date_raw": frame["date_raw"],
                    "army_id": 18, "native_carmy_id": 18, "owner_character_id": 31254,
                    "eligibility_mode": 1, "collection_filter_now": False, "collection_allow_guests": True,
                    "current_commander": {"status": "available", "character_id": 31254, "unavailable_reason": None},
                    "candidate_collection_complete": False, "candidate_source_count": 2,
                    "candidates": [], "unavailable_reason": "synthetic_partial_pool"}}
    def expenses():
        return {"status": "unavailable", "owner_character_id": 31254, "resource_id": "31254", "war_ids": [4],
                "raw_scale": 100000, "time_basis": "month", "source_scope": "actor_owned_military_once_across_all_wars",
                "future_war_cost_upper_ready": False, "resource_raw_native": None, "gold_raw": None,
                "treasury_raw": None, "unavailable_reason": "synthetic_not_required_for_R01"}
    cash = {**meta, "schema": "xar.ck3.war-cash-current-resources.v1", "game_version": "1.20.0.4",
            "executable_sha256": EXE_12004, "status": "partial", "snapshot_revision": 100,
            "date_raw": frame["date_raw"], "played_character_id": 31254,
            "read_only": True, "advertised": False, "formal_action_ready": False,
            "active_war_ids": [4], "player_army_ids": [18, 93],
            "current_treasury": {"raw": 2000000, "scale": 100000}, "player_monthly_net_income": None,
            "military_expenses": {"current": expenses(), "all_raised": expenses()}}
    counts = [{"territory_side": s, "eligible": n, "occupied": 0, "native_candidate_count": n, "collection_complete": True}
              for s, n in (("attacker", 0), ("defender", 1))]
    occupation = {**meta, "war_occupation_targets_v1": {"schema": "xar.ck3.war-occupation-targets.v1", "schema_version": 1,
        "game_version": "1.20.0.4", "executable_sha256": EXE_12004,
        "status": "available", "available": True, "collection_complete": True, "unavailable_reason": None,
        "snapshot_revision": 100, "date_raw": frame["date_raw"], "actor_character_id": 31254,
        "war_id": 4, "player_side": "attacker", "primary_attacker_character_id": 31254,
        "primary_defender_character_id": 34960, "side_counts": counts,
        "rows": [{"holding_title_id": 2192, "county_title_id": 2191, "province_id": 2635,
                  "legal_holder_character_id": 34960, "territory_side": "defender",
                  "occupation_observable": True, "is_occupied": False, "occupying_character_id": None,
                  "occupier_side": "none", "counted_occupied_by_opposing_side": False}]}}
    binding = {"machine_id": "synthetic-machine", "pid": 1234, "process_creation_filetime_100ns": 123,
               "connection_generation": 1, "episode_run_id": "synthetic-episode", "actor_id": 31254,
               "game_version": "1.20.0.4", "executable_sha256": EXE_12004,
               "normal_robert_source_receipt_sha256": "a"*64, "director_scope_revision": "synthetic-review"}
    return dict(before=frame, after=deepcopy(frame), strengths=query, commander=commander, cash=cash,
                occupation=occupation, source_binding=binding, army_id=18, native_carmy_id=18,
                war_id=4, goal_province_id=2635, staging_province_id=2645, agreed_commander_id=31254)


class ReadyT0NewBehavior(unittest.TestCase):
    def test_actual_regular1_accepts_and_legacy0_is_rejected(self):
        # R0180 day5/native boundary observed regular=1. This is a synthetic
        # semantic F using that real enum, not a new actual ready-T0 result.
        args = fixture()
        self.assertTrue(evaluate_episode04_ready_t0_12004(**args)["military_t0_frame_ready"])
        for frame in (args["before"], args["after"]):
            frame["player_armies"][0]["army_state_code"] = 0
        result = evaluate_episode04_ready_t0_12004(**args)
        self.assertFalse(result["military_t0_frame_ready"])
        self.assertIn("ready land state", result["missing_inputs"][0])

    def test_missing_troops_partial_pool_and_unrelated_battle_are_admitted(self):
        result = evaluate_episode04_ready_t0_12004(**fixture())
        self.assertTrue(result["military_t0_frame_ready"], result)
        self.assertEqual(result["full_DATA_empty_regiment_ids"], [55])
        self.assertFalse(result["r01_research_core_closed"])
        self.assertFalse(result["loss_sampling_ready"])

    def test_current_commander_must_be_same_frame_and_agreed(self):
        args = fixture(); args["commander"]["queried_native_revision"] = 99
        self.assertFalse(evaluate_episode04_ready_t0_12004(**args)["military_t0_frame_ready"])
        args = fixture(); args["agreed_commander_id"] = 34232
        self.assertIn("agreed", evaluate_episode04_ready_t0_12004(**args)["missing_inputs"][0])

    def test_moving_or_selected_combat_is_not_an_arrived_T0(self):
        args = fixture(); args["before"]["player_armies"][0].update(army_state="moving", army_state_code=7)
        self.assertFalse(evaluate_episode04_ready_t0_12004(**args)["military_t0_frame_ready"])
        args = fixture(); args["after"]["player_armies"][0]["in_combat"] = True
        self.assertFalse(evaluate_episode04_ready_t0_12004(**args)["military_t0_frame_ready"])

    def test_compact_summary_cannot_supply_F_DATA(self):
        args = fixture(); args["strengths"].pop("army_strengths")
        result = evaluate_episode04_ready_t0_12004(**args)
        self.assertIn("complete Driver", result["missing_inputs"][0])

    def test_unread_DATA_and_stale_cash_are_rejected(self):
        args = fixture(); data = args["strengths"]["army_strengths"][0]["regiment_replenishment_records_v1"][0]
        data.update(status="partial", ready=False, unavailable_reason="synthetic_unread")
        self.assertFalse(evaluate_episode04_ready_t0_12004(**args)["military_t0_frame_ready"])
        args = fixture(); args["cash"]["queried_snapshot_id"] = "native:99"
        self.assertFalse(evaluate_episode04_ready_t0_12004(**args)["military_t0_frame_ready"])

    def test_save_requires_the_actual_same_T0_epoch(self):
        args = fixture(); args["checkpoint"] = {"checkpoint": {"status": "saved", "date_raw": 53147520,
            "episode_character_id": 31254, "episode_run_id": "synthetic-episode", "size": 123,
            "sha256": "b"*64, "succession_lifecycle": {"lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off"}}}
        self.assertTrue(evaluate_episode04_ready_t0_12004(**args)["normal_t0_saved"])
        args["checkpoint"]["checkpoint"]["episode_run_id"] = "different-load"
        self.assertFalse(evaluate_episode04_ready_t0_12004(**args)["normal_t0_saved"])

    def test_request_recipe_is_readonly_and_uses_real_full_profile_parameters(self):
        requests = ready_t0_readonly_requests_12004(fixture()["before"], army_id=18, war_id=4)
        self.assertEqual(requests[0]["arguments"]["ordered_refill_entry_mode"], "observed_prepared")
        self.assertEqual(requests[0]["arguments"]["profile"], "observed_history_full_v1")
        self.assertEqual(requests[3]["arguments"]["step"], "query-war-occupation-targets-v1-4")
        self.assertNotIn("ck3_save_checkpoint", [r["tool"] for r in requests])

    def test_pending_save_does_not_crash_or_request_replay(self):
        args = fixture(); args["checkpoint"] = {"checkpoint": None, "status": "pending"}
        result = evaluate_episode04_ready_t0_12004(**args)
        self.assertTrue(result["military_t0_frame_ready"])
        self.assertFalse(result["normal_t0_saved"])
        self.assertIn("do not resubmit", result["missing_inputs"][0])


if __name__ == "__main__":
    unittest.main()
