from __future__ import annotations

from pathlib import Path
import copy
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.m5_joint_dispatch import M5FrameDispatcher
from xar_autoplayer.m5_observed_opportunity_selector import (
    active_defensive_war_continuation_proposal,
    construction_proposal,
    council_steward_proposal,
    faction_gift_proposal,
    observed_frame,
    select_observed_m5_opportunity,
    wartime_lifestyle_perk_proposal,
)
from xar_autoplayer.lifestyle_min_policy import choose_min_feudal_lifestyle_action


_FRAME = {
    "played_character_id": 29829,
    "native_revision": 9,
    "date_raw": 53178264,
    "snapshot_id": "native:9",
    "revision": 14,
    "episode_run_id": "native-29829-observed-joint",
}


def _snapshot(*, gold_raw: int = 40_000_000) -> dict[str, object]:
    return {
        **_FRAME,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 29829},
        "played_character_gold": {"raw": gold_raw, "scale": 100_000},
        "active_wars": [],
        "player_armies": [{"army_id": 71, "controllable": True}],
    }


def _commitments(**updates: object) -> dict[str, object]:
    value: dict[str, object] = {
        "frame": dict(_FRAME),
        "gold_raw": 0,
        "pending_war_slots": 0,
        "army_ids": [],
        "ally_character_ids": [],
        "character_ids": [],
        "commitment_keys": [],
    }
    value.update(updates)
    return value


def _council() -> dict[str, object]:
    return council_steward_proposal(
        frame=_FRAME,
        observation={
            "snapshot": {
                "snapshot_id": _FRAME["snapshot_id"],
                "public_revision": _FRAME["revision"],
                "native_revision": _FRAME["native_revision"],
                "date_raw": _FRAME["date_raw"],
                "paused": True,
            },
            "owner_character_id": _FRAME["played_character_id"],
            "position": {
                "incumbent_character_id": 41001,
                "incumbent_main_skill": {"key": "stewardship", "value": 8},
            },
            "candidate_collection_complete": True,
            "candidates": [{
                "character_id": 41002,
                "main_skill": {"key": "stewardship", "value": 17},
            }],
        },
        decision={
            "policy": "council-composition-steward-v1",
            "outcome": "REPLACE_REQUIRED",
            "action_routable": True,
            "required_capability": "game.action.assign-councillor-v1",
            "incumbent_character_id": 41001,
            "incumbent_main_skill": {"key": "stewardship", "value": 8},
            "selected_candidate": {
                "character_id": 41002,
                "main_skill": {"key": "stewardship", "value": 17},
            },
        },
    )


def _construction() -> dict[str, object]:
    return construction_proposal(
        frame=_FRAME,
        query={
            "status": "selected",
            "source_frame": {
                "snapshot_id": _FRAME["snapshot_id"],
                "revision": _FRAME["revision"],
                "native_revision": _FRAME["native_revision"],
                "date_raw": _FRAME["date_raw"],
                "episode_run_id": _FRAME["episode_run_id"],
                "actor_character_id": _FRAME["played_character_id"],
            },
            "candidate": {
                "barony_title_id": 501,
                "province_id": 601,
                "building_type_id": 701,
                "slot_index": 1,
                "stock_gold_cost_raw": 3_000_000,
                "gold_before_raw": 40_000_000,
            },
        },
    )


def _gift() -> dict[str, object]:
    return faction_gift_proposal(
        frame=_FRAME,
        candidate={
            "status": "selected",
            "choice": {
                "snapshot_revision": _FRAME["native_revision"],
                "native_snapshot_revision": _FRAME["native_revision"],
                "date_raw": _FRAME["date_raw"],
                "player_character_id": _FRAME["played_character_id"],
                "source_faction_id": 801,
                "recipient_character_id": 41003,
                "gold_cost_raw": 2_000_000,
                "opinion_delta": 20,
                "minimum_gold_reserve_raw": 10_000_000,
            },
        },
    )


def _defensive_snapshot() -> dict[str, object]:
    value = _snapshot()
    war = {
        "war_id": 16777231,
        "player_side": "defender",
        "player_is_primary_war_leader": True,
        "player_armies": [{"army_id": 71}],
    }
    value["active_wars"] = [war]
    return value


def _defensive_plan(*, selected_step: str = "query-war-termination-options-16777231") -> dict[str, object]:
    return {
        "policy": "one-life-turn-v1",
        "phase": "native_war_termination_query",
        "selected_step": selected_step,
        "war_id": 16777231,
        "active_wars": [{
            "war_id": 16777231,
            "player_side": "defender",
            "player_is_primary_war_leader": True,
        }],
    }


def _continuation_observation(**updates: object) -> dict[str, object]:
    value: dict[str, object] = {
        "status": "available", "read_only": True,
        "source_frame": dict(_FRAME), "war_id": 16777231,
        "army_ids": [71], "ally_character_ids": [],
        "army_war_bindings": [{"army_id": 71, "war_id": 16777231}],
        "character_ids": [30097],
        "projected_supply_margin_raw": 250_000,
        "incremental_gold_cost_raw": 0,
        "minimum_gold_reserve_raw": 5_000_000,
    }
    value.update(updates)
    return value


def _wartime_lifestyle() -> tuple[dict[str, object], dict[str, object]]:
    life = {
        "status": "available", "snapshot_id": _FRAME["snapshot_id"],
        "episode_run_id": _FRAME["episode_run_id"],
        "public_revision": _FRAME["native_revision"],
        "native_revision": _FRAME["native_revision"],
        "proof_epoch": _FRAME["native_revision"],
        "date_raw": _FRAME["date_raw"],
        "player_character_id": _FRAME["played_character_id"],
        "current_focus": {
            "presence": "present", "key": "stewardship_wealth_focus",
            "lifestyle_key": "stewardship_lifestyle",
        },
        "current_lifestyle_progress": {
            "presence": "present", "lifestyle_key": "stewardship_lifestyle",
            "unspent_perk_points": 1, "used_perk_points": 5,
        },
        "owned_perk_keys": ["tax_man_perk"],
        "legal_perk_candidates": {"status": "available", "items": [{
            "key": "cutting_corners_perk",
            "lifestyle_key": "stewardship_lifestyle",
        }]},
        "readiness": {key: True for key in (
            "current_focus_ready", "lifestyle_progress_ready",
            "owned_perks_ready", "legal_perk_candidates_ready",
            "same_frame_ready",
        )},
    }
    decision = choose_min_feudal_lifestyle_action(
        life, feudal_scope_admitted=True, at_peace=False,
        allow_wartime_perk=True,
    )
    return ({
        "status": "available", "formal_precondition_status": "ready",
        "episode_run_id": _FRAME["episode_run_id"],
        "source_frame": {
            "snapshot_id": _FRAME["snapshot_id"],
            "revision": _FRAME["revision"],
            "native_revision": _FRAME["native_revision"],
            "date_raw": _FRAME["date_raw"],
            "player_character_id": _FRAME["played_character_id"],
        },
        "snapshot": life,
    }, decision)


class M5ObservedOpportunitySelectorTests(unittest.TestCase):
    def test_formal_adapters_preserve_observed_fields_without_utility(self) -> None:
        council, building, gift = _council(), _construction(), _gift()
        self.assertEqual(council["evidence"]["candidate_stewardship"], 17)
        self.assertEqual(building["gold_cost_raw"], 3_000_000)
        self.assertEqual(gift["evidence"]["opinion_delta"], 20)
        for row in (council, building, gift):
            self.assertNotIn("benefit_units", row)
            self.assertNotIn("utility", row)

    def test_observed_commitment_conflict_changes_formal_candidate_selection(self) -> None:
        proposals = [_council(), _construction(), _gift()]
        open_result = select_observed_m5_opportunity(
            snapshot=_snapshot(), proposals=proposals,
            commitments=_commitments(), gold_reserve_raw=5_000_000,
            max_active_wars=1,
        )
        self.assertEqual(open_result["selected_candidate_id"],
                         "council:steward:41002")

        reserved_result = select_observed_m5_opportunity(
            snapshot=_snapshot(), proposals=proposals,
            commitments=_commitments(
                commitment_keys=["council-seat:councillor_steward"]),
            gold_reserve_raw=5_000_000, max_active_wars=1,
        )
        reasons = {row["domain"]: row["reason"]
                   for row in reserved_result["evaluated"]}
        self.assertEqual(reasons["council"], "existing_commitment_conflict")
        self.assertEqual(reserved_result["selected_candidate_id"],
                         "diplomacy:faction-gift:801:41003")

    def test_dispatch_reserves_one_observed_choice_and_shared_resources(self) -> None:
        dispatcher = M5FrameDispatcher(
            snapshot=_snapshot(), existing_commitments=_commitments(
                commitment_keys=["council-seat:councillor_steward"]),
        )
        first = dispatcher.choose_observed(
            snapshot=_snapshot(), proposals=[_council(), _construction(), _gift()],
            gold_reserve_raw=5_000_000, max_active_wars=1,
        )
        self.assertEqual(first["status"], "reserved_observed_analytic")
        self.assertEqual(first["selected_candidate_id"],
                         "diplomacy:faction-gift:801:41003")
        after = first["reservation"]["commitments_after"]
        self.assertEqual(after["gold_raw"], 2_000_000)
        self.assertEqual(after["character_ids"], [41003])
        self.assertIn("faction-gift:801:41003", after["commitment_keys"])
        second = dispatcher.choose_observed(
            snapshot=_snapshot(), proposals=[_construction()],
            gold_reserve_raw=5_000_000, max_active_wars=1,
        )
        self.assertEqual(second["status"], "already_reserved_this_frame")
        self.assertIsNone(second["selected_candidate_id"])
        self.assertFalse(first["formal_action_ready"])

    def test_budget_rejection_moves_to_a_lower_cost_ready_candidate(self) -> None:
        expensive = _construction()
        expensive["gold_cost_raw"] = 16_000_001
        result = select_observed_m5_opportunity(
            snapshot=_snapshot(gold_raw=36_000_000),
            proposals=[expensive, _gift()], commitments=_commitments(),
            gold_reserve_raw=5_000_000, max_active_wars=1,
        )
        by_domain = {row["domain"]: row for row in result["evaluated"]}
        self.assertEqual(by_domain["building"]["reason"], "shared_gold_budget")
        self.assertEqual(result["selected_candidate_id"],
                         "diplomacy:faction-gift:801:41003")

    def test_war_and_marriage_require_missing_material_observations(self) -> None:
        base = _gift()
        war = copy.deepcopy(base)
        war.update({
            "candidate_id": "war:31549-40--1", "domain": "war",
            "source_policy": "conservative-war-entry",
            "war_slot_claim": 1, "army_ids": [],
            "projected_supply_margin_raw": None,
        })
        with self.assertRaisesRegex(ValueError, "measured supply"):
            select_observed_m5_opportunity(
                snapshot=_snapshot(), proposals=[war], commitments=_commitments(),
                gold_reserve_raw=5_000_000, max_active_wars=1,
            )
        marriage = copy.deepcopy(base)
        marriage.update({
            "candidate_id": "marriage:38822-16778038",
            "domain": "marriage", "source_policy": "first-heir-marriage-v1",
            "gold_cost_raw": 0, "character_ids": [38822],
            "commitment_keys": [],
        })
        with self.assertRaisesRegex(ValueError, "marriage proposal lacks"):
            select_observed_m5_opportunity(
                snapshot=_snapshot(), proposals=[marriage],
                commitments=_commitments(), gold_reserve_raw=5_000_000,
                max_active_wars=1,
            )

    def test_existing_defensive_war_uses_no_new_slot_but_keeps_army_cost(self) -> None:
        snapshot = _defensive_snapshot()
        continuation = active_defensive_war_continuation_proposal(
            frame=_FRAME, snapshot=snapshot, plan=_defensive_plan(),
            observation=_continuation_observation(),
        )
        self.assertEqual(continuation["war_slot_claim"], 0)
        self.assertEqual(continuation["war_operation"],
                         "active_defensive_continuation")
        self.assertEqual(continuation["army_ids"], [71])
        self.assertIn("active-war:16777231", continuation["commitment_keys"])
        result = select_observed_m5_opportunity(
            snapshot=snapshot, proposals=[continuation],
            commitments=_commitments(), gold_reserve_raw=5_000_000,
            max_active_wars=1,
        )
        self.assertEqual(result["status"], "selected")
        self.assertEqual(result["evaluated"][0]["reason"], "eligible")

    def test_defensive_continuation_refuses_missing_supply_observation(self) -> None:
        observation = _continuation_observation()
        observation["projected_supply_margin_raw"] = None
        with self.assertRaisesRegex(ValueError, "measured supply"):
            active_defensive_war_continuation_proposal(
                frame=_FRAME, snapshot=_defensive_snapshot(),
                plan=_defensive_plan(), observation=observation,
            )

    def test_query_only_war_allows_observed_zero_date_perk_opportunity(self) -> None:
        snapshot = _defensive_snapshot()
        continuation = active_defensive_war_continuation_proposal(
            frame=_FRAME, snapshot=snapshot, plan=_defensive_plan(),
            observation=_continuation_observation(),
        )
        query, decision = _wartime_lifestyle()
        lifestyle = wartime_lifestyle_perk_proposal(
            frame=_FRAME, query=query, decision=decision,
            current_war_plan=_defensive_plan(),
        )
        self.assertEqual(lifestyle["evidence"]["unspent_perk_points"], 1)
        self.assertEqual(lifestyle["evidence"]["used_perk_points"], 5)
        self.assertFalse(lifestyle["evidence"]["date_advance_expected"])
        self.assertEqual(lifestyle["commitment_keys"], [
            "lifestyle-perk-point:stewardship_lifestyle"
        ])
        result = select_observed_m5_opportunity(
            snapshot=snapshot, proposals=[continuation, lifestyle],
            commitments=_commitments(), gold_reserve_raw=5_000_000,
            max_active_wars=1,
        )
        self.assertEqual(result["selected_candidate_id"],
                         "lifestyle:perk:cutting_corners_perk")
        by_id = {row["candidate_id"]: row for row in result["evaluated"]}
        self.assertEqual(by_id["war:continue:defender:16777231"]["reason"],
                         "eligible")

    def test_war_gameplay_step_prevents_lifestyle_admission(self) -> None:
        query, decision = _wartime_lifestyle()
        with self.assertRaisesRegex(ValueError, "war gameplay step has priority"):
            wartime_lifestyle_perk_proposal(
                frame=_FRAME, query=query, decision=decision,
                current_war_plan=_defensive_plan(
                    selected_step="move-army-71-to-2619"),
            )

    def test_full_frame_identity_is_required(self) -> None:
        stale = _gift()
        stale["frame"] = {**observed_frame(_snapshot()), "revision": 15}
        with self.assertRaisesRegex(ValueError, "same-frame proposal"):
            select_observed_m5_opportunity(
                snapshot=_snapshot(), proposals=[stale],
                commitments=_commitments(), gold_reserve_raw=5_000_000,
                max_active_wars=1,
            )


if __name__ == "__main__":
    unittest.main()
