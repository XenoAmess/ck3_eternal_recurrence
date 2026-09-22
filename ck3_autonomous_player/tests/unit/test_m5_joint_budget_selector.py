from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.m5_joint_budget_selector import select_m5_assessed_candidate


# Five IDs and this war declaration were observed together in R736 native:3.
# All utility/resource numbers below are synthetic assessor inputs.  R736 did
# not record current gold or the missing value/supply/commitment readbacks.
_HEIR = 38822
_FAMILY_IDS = [16778038, 16778252, 16778632, 16778730, 16778737]
_WAR_ID = "29097-11-0"


def _intake() -> dict[str, object]:
    return {
        "policy": "g2-m5-same-frame-intake-v1", "played_character_id": 29829,
        "native_revision": 3, "date_raw": 53178264,
        "candidates": [
            {"candidate_id": f"first-heir-marriage:{_HEIR}-{candidate_id}",
             "domain": "first_heir_marriage", "subject_character_id": _HEIR,
             "candidate_character_id": candidate_id}
            for candidate_id in _FAMILY_IDS
        ] + [{"candidate_id": f"war:{_WAR_ID}", "domain": "war"}],
    }


def _snapshot(*, gold_raw: int = 9_000_000, active_wars: list | None = None) -> dict[str, object]:
    return {
        "paused": True, "map_ready": True, "played_character": {"character_id": 29829},
        "native_revision": 3, "date_raw": 53178264,
        "played_character_gold": {"raw": gold_raw, "scale": 100_000},
        "active_wars": [] if active_wars is None else active_wars,
        "player_armies": [{"army_id": 11, "controllable": True}],
    }


def _commitments() -> dict[str, object]:
    return {
        "gold_raw": 1_000_000, "army_ids": [], "ally_character_ids": [],
        "character_ids": [], "commitment_keys": [],
    }


def _assessment(candidate: dict[str, object], *, benefit: int) -> dict[str, object]:
    family = candidate["domain"] == "first_heir_marriage"
    return {
        "candidate_id": candidate["candidate_id"], "played_character_id": 29829,
        "native_revision": 3, "date_raw": 53178264,
        "benefit_units": benefit, "war_cost_units": 0,
        "family_cost_units": 0, "diplomacy_cost_units": 0,
        "supply_cost_units": 0, "long_term_cost_units": 1,
        "gold_raw": 0, "projected_supply_margin_units": 0,
        "army_ids": [], "ally_character_ids": [],
        "character_ids": [_HEIR, candidate["candidate_character_id"]] if family else [],
        "commitment_keys": [],
    }


def _assessments() -> list[dict[str, object]]:
    rows = _intake()["candidates"]
    return [_assessment(row, benefit=2 + index) for index, row in enumerate(rows)]


def _select(**changes: object) -> dict[str, object]:
    args: dict[str, object] = {
        "intake": _intake(), "snapshot": _snapshot(),
        "assessments": _assessments(), "commitments": _commitments(),
        "gold_reserve_raw": 2_000_000, "max_active_wars": 1,
    }
    args.update(changes)
    return select_m5_assessed_candidate(**args)


class M5JointBudgetSelectorTests(unittest.TestCase):
    def test_observed_same_frame_candidate_ids_select_one_assessed_alternative(self) -> None:
        result = _select()
        self.assertEqual(result["selected_candidate_id"], f"war:{_WAR_ID}")
        self.assertEqual(result["assessed_candidate_count"], 6)
        self.assertEqual(result["unassessed_legal_candidate_count"], 0)
        self.assertIsNone(result["selected_step"])
        self.assertFalse(result["formal_action_ready"])

    def test_shared_gold_war_slot_supply_and_existing_commitments_change_choice(self) -> None:
        rows = _assessments()
        rows[-1]["gold_raw"] = 7_000_001  # gold - reserve - existing commitment
        result = _select(assessments=rows)
        self.assertEqual(result["evaluated"][-1]["reason"], "shared_gold_budget")
        self.assertEqual(result["selected_candidate_id"], rows[-2]["candidate_id"])

        rows[-1]["gold_raw"] = 0
        rows[-1]["projected_supply_margin_units"] = -1
        result = _select(assessments=rows)
        self.assertEqual(result["evaluated"][-1]["reason"], "projected_supply_deficit")

        rows[-1]["projected_supply_margin_units"] = 0
        result = _select(assessments=rows, snapshot=_snapshot(active_wars=[{"war_id": 22}]))
        self.assertEqual(result["evaluated"][-1]["reason"], "war_slot_budget")

        reserved = _commitments()
        reserved["character_ids"] = [_HEIR]
        reserved["army_ids"] = [11]
        rows[-1]["army_ids"] = [11]
        result = _select(assessments=rows, commitments=reserved)
        self.assertEqual(result["status"], "wait")
        self.assertTrue(all(row["reason"] == "existing_commitment_conflict" for row in result["evaluated"]))

    def test_ally_and_long_term_claims_are_exclusive(self) -> None:
        rows = _assessments()
        rows[-1]["ally_character_ids"] = [40010]
        rows[-1]["commitment_keys"] = ["diplomatic-slot:40010"]
        reserved = _commitments()
        reserved["ally_character_ids"] = [40010]
        result = _select(assessments=rows, commitments=reserved)
        self.assertEqual(result["evaluated"][-1]["reason"], "existing_commitment_conflict")
        reserved["ally_character_ids"] = []
        reserved["commitment_keys"] = ["diplomatic-slot:40010"]
        result = _select(assessments=rows, commitments=reserved)
        self.assertEqual(result["evaluated"][-1]["reason"], "existing_commitment_conflict")

    def test_nonpositive_value_waits_but_positive_feasible_value_does_not(self) -> None:
        rows = _assessments()
        for row in rows:
            row["benefit_units"] = 1
        self.assertEqual(_select(assessments=rows)["status"], "wait")
        rows[0]["benefit_units"] = 2
        self.assertEqual(_select(assessments=rows)["selected_candidate_id"], rows[0]["candidate_id"])

    def test_stale_frame_and_missing_assessments_never_suggest_a_step(self) -> None:
        snapshot = _snapshot()
        snapshot["date_raw"] += 24
        with self.assertRaisesRegex(ValueError, "crossed the paused native frame"):
            _select(snapshot=snapshot)
        result = _select(assessments=[])
        self.assertEqual(result["status"], "missing_assessments")
        self.assertIsNone(result["selected_candidate_id"])
        self.assertIsNone(result["selected_step"])

    def test_r736_missing_current_treasury_cannot_be_treated_as_zero(self) -> None:
        snapshot = _snapshot()
        snapshot.pop("played_character_gold")
        with self.assertRaisesRegex(ValueError, "played_character_gold"):
            _select(snapshot=snapshot)


if __name__ == "__main__":
    unittest.main()
