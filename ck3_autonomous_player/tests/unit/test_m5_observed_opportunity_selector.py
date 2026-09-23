from __future__ import annotations

from pathlib import Path
import copy
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.m5_joint_dispatch import M5FrameDispatcher
from xar_autoplayer.m5_observed_opportunity_selector import (
    construction_proposal,
    council_steward_proposal,
    faction_gift_proposal,
    observed_frame,
    select_observed_m5_opportunity,
)


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
