from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.marriage_matchmaking_contract import (
    normalize_ranked_marriage_observation,
)
from xar_autoplayer.joint_candidate_ledger import build_joint_candidate_ledger


def _marriage_row(rank: int, candidate: int, *, legal: bool = True) -> dict[str, object]:
    return {
        "rank": rank,
        "subject_character_id": 29829,
        "matchmaker_character_id": 29829,
        "candidate_character_id": candidate,
        "native_candidate_score": 100 - rank,
        "pair_roles": {
            "actor_character_id": 29829,
            "recipient_character_id": candidate,
            "secondary_actor_character_id": 29829,
            "secondary_recipient_character_id": candidate,
            "intermediary_character_id": 0,
        },
        "complete_can_send": legal,
        "complete_can_send_status_raw": 0,
        "recipient_ai_accept_raw": 250000,
        "recipient_ai_accept_scale": 100000,
        "recipient_answer_status_raw": 0,
        "recipient_answer_allows_send": legal,
        "predicted_outcome": "marriage",
    }


def _observation(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "private_build": True,
        "advertised": False,
        "status": "available",
        "exact_build": "1.19.0.6",
        "snapshot_id": "native:693",
        "public_revision": 693,
        "native_revision": 693,
        "proof_epoch": 4,
        "date_raw": 53178264,
        "subject_character_id": 29829,
        "matchmaker_character_id": 29829,
        "religion_projection": "native_final_results_only",
        "candidates": rows,
        "readiness": {
            key: True
            for key in (
                "ranked_candidates_ready", "pair_character_ids_ready", "native_score_ready",
                "complete_can_send_ready", "recipient_ai_accept_ready",
                "recipient_answer_ready", "predicted_outcome_ready", "same_frame_ready",
            )
        },
    }


def _normalize(raw: dict[str, object]) -> dict[str, object]:
    return normalize_ranked_marriage_observation(
        raw,
        snapshot_id="native:693",
        public_revision=693,
        native_revision=693,
        date_raw=53178264,
        played_character_id=29829,
    )


def _war(declaration_id: str, target: int) -> dict[str, object]:
    return {
        "declaration_id": declaration_id,
        "target_character_id": target,
        "casus_belli_index": 11,
        "casus_belli_key": "claim_cb",
        "configuration_index": 0,
        "claimant_character_id": -1,
        "target_title_ids": [2121],
    }


class JointCandidateLedgerTests(unittest.TestCase):
    def test_five_gate_counts_distinct_native_legal_rows_only(self) -> None:
        marriage = _normalize(_observation([
            _marriage_row(1, 30001), _marriage_row(2, 30002),
            _marriage_row(3, 30003, legal=False), _marriage_row(4, 30004),
        ]))
        wars = [_war("31001-11-0", 31001), _war("31002-11-0", 31002)]
        result = build_joint_candidate_ledger(
            ranked_marriage=marriage,
            declarable_wars=wars,
            available_steps={"arrange-marriage-29829-30001", "declare-war-31001-11-0"},
            active_wars=[{"war_id": 33554527}],
        )
        self.assertEqual(result["native_legal_candidate_count"], 5)
        self.assertTrue(result["minimum_five_native_legal_candidates_observed"])
        self.assertFalse(result["joint_selection_ready"])
        self.assertIsNone(result["selected_step"])
        self.assertEqual([row["domain"] for row in result["candidates"]],
                         ["marriage", "marriage", "marriage", "war", "war"])
        self.assertEqual(result["candidates"][-1]["existing_war_count"], 1)

    def test_stale_or_relabelled_ranked_frame_cannot_enter_ledger(self) -> None:
        raw = _observation([_marriage_row(4, 30004)])
        raw["date_raw"] += 24
        with self.assertRaisesRegex(ValueError, "current played-character frame"):
            _normalize(raw)
        raw = _observation([_marriage_row(4, 30004)])
        raw["candidates"][0]["pair_roles"]["secondary_recipient_character_id"] = 30005
        with self.assertRaisesRegex(ValueError, "actual pair"):
            _normalize(raw)

    def test_filtered_native_rank_and_unsigned_intermediary_are_preserved(self) -> None:
        row = _marriage_row(4, 30004)
        row["pair_roles"]["intermediary_character_id"] = 2**32 - 1
        normalized = _normalize(_observation([row]))
        self.assertEqual(normalized["candidates"][0]["rank"], 4)
        self.assertEqual(normalized["candidates"][0]["pair_roles"]["intermediary_character_id"], 2**32 - 1)

    def test_illegal_and_duplicate_rows_cannot_fill_five_gate(self) -> None:
        marriage = _normalize(_observation([_marriage_row(1, 30001, legal=False), _marriage_row(2, 30002)]))
        result = build_joint_candidate_ledger(
            ranked_marriage=marriage, declarable_wars=[], available_steps=set(), active_wars=[])
        self.assertEqual(result["native_legal_candidate_count"], 1)
        self.assertFalse(result["minimum_five_native_legal_candidates_observed"])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            _normalize(_observation([_marriage_row(1, 30001), _marriage_row(2, 30001)]))


if __name__ == "__main__":
    unittest.main()
