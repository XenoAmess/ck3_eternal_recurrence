from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.m5_joint_intake import build_m5_same_frame_intake


# Five distinct rows transcribed from the immutable R0082 typed result
# D7C3FE9BC820983BE6E747A2415DCDDC69F4FD5A10E88D65DC4543759A8B698A.
_R0082_IDS = [16778038, 16778252, 16778632, 16778730, 16778737]
_R0082_ACCEPT_RAW = [3600000, 1600000, 3400000, 4100000, 4300000]


def _frame(*, date_raw: int = 53178264, episode_run_id: str = "fixture-episode") -> dict[str, object]:
    return {
        "paused": True, "map_ready": True, "native_revision": 3,
        "date_raw": date_raw, "played_character": {"character_id": 29829},
        "snapshot_id": "native:3", "revision": 4,
        "episode_run_id": episode_run_id,
    }


def _family() -> dict[str, object]:
    rows = [{
        "played_character_id": 29829,
        "subject_character_id": 38822,
        "candidate_character_id": candidate_id,
        "native_rank": None,
        "complete_can_send": True,
        "recipient_ai_accept_raw": accept_raw,
        "recipient_answer_allows_send": True,
    } for candidate_id, accept_raw in zip(_R0082_IDS, _R0082_ACCEPT_RAW)]
    return {
        "schema": "xar.ck3.observed-first-heir-marriage-legality.v1",
        "exact_ck3_build": "1.19.0.6",
        "read_only": True, "advertised": False, "status": "available",
        "native_revision": 3, "observed_first_heir_character_id": 38822,
        "native_legal_candidates": rows,
    }


def _war_query() -> dict[str, object]:
    return {
        "step": "query-declarable-wars", "accepted": True,
        "status": "available", "declarable_wars": [{
            "declaration_id": "31050-11-0",
            "target_character_id": 31050,
            "casus_belli_index": 11,
            "casus_belli_key": "claim_cb",
            "configuration_index": 0,
            "claimant_character_id": 29829,
            "target_title_ids": [2132],
        }],
    }


class M5SameFrameIntakeTests(unittest.TestCase):
    def test_real_first_heir_rows_are_unranked_and_do_not_select_an_action(self) -> None:
        result = build_m5_same_frame_intake(
            before=_frame(), after=_frame(),
            first_heir_legality=_family(), declarable_war_query=_war_query(),
        )
        self.assertEqual(result["family_candidate_count"], 5)
        self.assertEqual(result["war_candidate_count"], 1)
        self.assertEqual(result["native_legal_candidate_count"], 6)
        self.assertTrue(result["minimum_five_native_legal_candidates_observed"])
        self.assertEqual(
            {row["candidate_character_id"] for row in result["candidates"][:5]},
            set(_R0082_IDS),
        )
        self.assertTrue(all(row["native_rank"] is None for row in result["candidates"][:5]))
        self.assertFalse(result["joint_selection_ready"])
        self.assertIsNone(result["selected_step"])
        self.assertEqual(result["episode_run_id"], "fixture-episode")

    def test_changed_date_cannot_reuse_five_current_candidates(self) -> None:
        with self.assertRaisesRegex(ValueError, "crossed a paused native frame"):
            build_m5_same_frame_intake(
                before=_frame(), after=_frame(date_raw=53178288),
                first_heir_legality=_family(), declarable_war_query=_war_query(),
            )

    def test_changed_episode_cannot_reuse_same_date_and_native_revision(self) -> None:
        with self.assertRaisesRegex(ValueError, "crossed a paused native frame"):
            build_m5_same_frame_intake(
                before=_frame(), after=_frame(episode_run_id="new-episode"),
                first_heir_legality=_family(), declarable_war_query=_war_query(),
            )

    def test_rank_or_duplicate_does_not_relabel_unranked_family_inventory(self) -> None:
        family = _family()
        family["native_legal_candidates"][1]["candidate_character_id"] = _R0082_IDS[0]
        with self.assertRaisesRegex(ValueError, "duplicated, stale, ranked"):
            build_m5_same_frame_intake(
                before=_frame(), after=_frame(),
                first_heir_legality=family, declarable_war_query=_war_query(),
            )
        family = _family()
        family["native_legal_candidates"][0]["native_rank"] = 1
        with self.assertRaisesRegex(ValueError, "duplicated, stale, ranked"):
            build_m5_same_frame_intake(
                before=_frame(), after=_frame(),
                first_heir_legality=family, declarable_war_query=_war_query(),
            )


if __name__ == "__main__":
    unittest.main()
