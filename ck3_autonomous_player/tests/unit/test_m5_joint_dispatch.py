from __future__ import annotations

from pathlib import Path
import copy
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.m5_joint_dispatch import (
    M5FrameDispatcher, summarize_m5_alliance_readback,
)


# IDs/frame are an excerpt of immutable R0133 report CFE56353...B3B9 and
# projection C58A3279...CF3A.  R0133 did not retain same-frame war/gold,
# campaign values or commitments; the complete scenarios below are synthetic.
_FRAME = {
    "played_character_id": 29829, "native_revision": 3,
    "date_raw": 53178264, "snapshot_id": "native:3", "revision": 4,
    "episode_run_id": "native-29829-5e02a8fc4bfa",
}
_HEIR = 38822
_FAMILY = [16778038, 16778252, 16778632, 16778730, 16778737]


def _r0133_readbacks() -> tuple[dict[str, object], dict[str, object]]:
    legality = {
        "schema": "xar.ck3.observed-first-heir-marriage-legality.v1",
        "exact_ck3_build": "1.19.0.6", "read_only": True,
        "advertised": False, "status": "available", "native_revision": 3,
        "query_sequence": 1, "observed_first_heir_character_id": _HEIR,
        "native_legal_candidates": [
            {"played_character_id": 29829, "subject_character_id": _HEIR,
             "candidate_character_id": candidate,
             "complete_can_send": True, "recipient_answer_allows_send": True}
            for candidate in _FAMILY
        ],
    }
    projection = {
        "schema": "xar.ck3.first-heir-candidate-alliance-projection.v1",
        "exact_ck3_build": "1.19.0.6", "read_only": True,
        "advertised": False, "status": "available", "native_revision": 3,
        "legality_query_sequence": 1,
        "rows": [
            {"actor_character_id": 29829, "heir_character_id": _HEIR,
             "candidate_character_id": candidate, "status": "available",
             "possible_alliance_pairs": [
                 {"first_character_id": 29829 if index == 0 else candidate,
                  "second_character_id": candidate if index == 0 else _HEIR,
                  "already_allied": False, "both_have_realm_data": False,
                  "would_attempt_if_accepted": False}
                 for index in range(count)
             ]}
            for candidate, count in zip(_FAMILY, (1, 2, 2, 2, 1))
        ],
    }
    return legality, projection


def _snapshot(*, resources: bool) -> dict[str, object]:
    result = {
        **_FRAME, "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829},
    }
    if resources:
        result.update({
            "played_character_gold": {"raw": 9_000_000, "scale": 100_000},
            "active_wars": [],
            "player_armies": [{"army_id": 11, "controllable": True}],
        })
    return result


def _intake(*, synthetic_war: bool) -> dict[str, object]:
    rows = [
        {"candidate_id": f"first-heir-marriage:{_HEIR}-{candidate}",
         "domain": "first_heir_marriage", "subject_character_id": _HEIR,
         "candidate_character_id": candidate}
        for candidate in _FAMILY
    ]
    if synthetic_war:
        rows.append({"candidate_id": "war:fixture-declaration", "domain": "war"})
    return {**_FRAME, "policy": "g2-m5-same-frame-intake-v1", "candidates": rows}


def _commitments() -> dict[str, object]:
    return {
        "frame": _FRAME.copy(),
        "gold_raw": 1_000_000, "pending_war_slots": 0,
        "army_ids": [], "ally_character_ids": [], "character_ids": [],
        "commitment_keys": [],
    }


def _assessments() -> list[dict[str, object]]:
    rows = []
    for index, candidate in enumerate(_intake(synthetic_war=True)["candidates"]):
        family = candidate["domain"] == "first_heir_marriage"
        rows.append({
            **_FRAME, "candidate_id": candidate["candidate_id"],
            "benefit_units": index + 2 if family else 20,
            "war_cost_units": 0 if family else 2,
            "family_cost_units": 0, "diplomacy_cost_units": 0 if family else 2,
            "supply_cost_units": 0 if family else 2,
            "long_term_cost_units": 1 if family else 3,
            "gold_raw": 0 if family else 2_000_000,
            "projected_supply_margin_units": 0 if family else 1,
            "army_ids": [] if family else [11],
            "ally_character_ids": [] if family else [444],
            "character_ids": [_HEIR, candidate["candidate_character_id"]] if family else [],
            "commitment_keys": [] if family else ["treaty:444"],
        })
    return rows


def _choose(
    dispatcher: M5FrameDispatcher, *, snapshot: dict[str, object] | None = None,
    assessments: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return dispatcher.choose(
        intake=_intake(synthetic_war=True),
        snapshot=_snapshot(resources=True) if snapshot is None else snapshot,
        assessments=_assessments() if assessments is None else assessments,
        gold_reserve_raw=2_000_000, max_active_wars=1,
    )


class M5JointDispatchTests(unittest.TestCase):
    def test_r0133_projection_has_no_observed_alliance_payoff(self) -> None:
        legality, projection = _r0133_readbacks()
        result = summarize_m5_alliance_readback(
            legality=legality, projection=projection)
        self.assertEqual(result["candidate_character_ids"], _FAMILY)
        self.assertEqual(result["possible_pair_count"], 8)
        self.assertEqual(result["would_attempt_pair_count"], 0)
        self.assertFalse(result["alliance_payoff_ready"])
        self.assertFalse(result["long_term_commitment_ready"])
        projection["legality_query_sequence"] = 2
        with self.assertRaisesRegex(ValueError, "one native legal frame"):
            summarize_m5_alliance_readback(
                legality=legality, projection=projection)

    def test_r0133_readback_alone_does_not_invent_a_joint_choice(self) -> None:
        snapshot = _snapshot(resources=False)
        dispatcher = M5FrameDispatcher(
            snapshot=snapshot, existing_commitments=_commitments())
        result = dispatcher.choose(
            intake=_intake(synthetic_war=False), snapshot=snapshot,
            assessments=[], gold_reserve_raw=2_000_000, max_active_wars=1)
        self.assertEqual(result["status"], "missing_assessments")
        self.assertIsNone(result["selected_candidate_id"])
        self.assertIsNone(result["reservation"])
        self.assertFalse(result["formal_action_ready"])

    def test_complete_fixture_selects_once_and_reserves_shared_resources(self) -> None:
        dispatcher = M5FrameDispatcher(
            snapshot=_snapshot(resources=True), existing_commitments=_commitments())
        first = _choose(dispatcher)
        self.assertEqual(first["status"], "reserved_analytic")
        self.assertEqual(first["selected_candidate_id"], "war:fixture-declaration")
        reserved = first["reservation"]
        self.assertEqual(reserved["commitments_after"]["gold_raw"], 3_000_000)
        self.assertEqual(reserved["commitments_after"]["pending_war_slots"], 1)
        self.assertEqual(reserved["commitments_after"]["army_ids"], [11])
        self.assertEqual(reserved["commitments_after"]["ally_character_ids"], [444])
        self.assertEqual(reserved["commitments_after"]["commitment_keys"], ["treaty:444"])
        self.assertIsNone(first["selected_step"])
        self.assertFalse(first["formal_action_ready"])
        second = _choose(dispatcher)
        self.assertEqual(second["status"], "already_reserved_this_frame")
        self.assertIsNone(second["selected_candidate_id"])
        self.assertEqual(second["reservation"], reserved)

    def test_existing_ally_or_pending_war_claim_moves_choice_to_family(self) -> None:
        claims = _commitments()
        claims["ally_character_ids"] = [444]
        dispatcher = M5FrameDispatcher(
            snapshot=_snapshot(resources=True), existing_commitments=claims)
        result = _choose(dispatcher)
        self.assertEqual(result["analysis"]["evaluated"][-1]["reason"],
                         "existing_commitment_conflict")
        self.assertEqual(result["selected_candidate_id"],
                         f"first-heir-marriage:{_HEIR}-{_FAMILY[-1]}")

        claims = _commitments()
        claims["pending_war_slots"] = 1
        dispatcher = M5FrameDispatcher(
            snapshot=_snapshot(resources=True), existing_commitments=claims)
        result = _choose(dispatcher)
        self.assertEqual(result["analysis"]["evaluated"][-1]["reason"],
                         "war_slot_budget")
        self.assertEqual(result["reservation"]["commitments_after"]["pending_war_slots"], 1)

    def test_cross_episode_assessment_and_snapshot_are_rejected(self) -> None:
        dispatcher = M5FrameDispatcher(
            snapshot=_snapshot(resources=True), existing_commitments=_commitments())
        rows = _assessments()
        rows[0]["episode_run_id"] = "other-episode"
        with self.assertRaisesRegex(ValueError, "crossed an episode"):
            _choose(dispatcher, assessments=rows)
        snapshot = copy.deepcopy(_snapshot(resources=True))
        snapshot["episode_run_id"] = "other-episode"
        with self.assertRaisesRegex(ValueError, "crossed an episode"):
            _choose(dispatcher, snapshot=snapshot)

    def test_missing_explicit_pending_commitment_is_not_zero(self) -> None:
        claims = _commitments()
        del claims["pending_war_slots"]
        with self.assertRaisesRegex(ValueError, "must be explicit"):
            M5FrameDispatcher(snapshot=_snapshot(resources=True),
                              existing_commitments=claims)

    def test_stale_commitment_readback_is_rejected(self) -> None:
        claims = _commitments()
        claims["frame"]["episode_run_id"] = "other-episode"
        with self.assertRaisesRegex(ValueError, "commitments crossed"):
            M5FrameDispatcher(snapshot=_snapshot(resources=True),
                              existing_commitments=claims)


if __name__ == "__main__":
    unittest.main()
