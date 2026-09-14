from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.succession_transition_contract import (
    SUCCESSION_EXPECTATION_V1_SCHEMA,
    SUCCESSION_RECONCILIATION_V1_SCHEMA,
    freeze_succession_expectation_v1,
    reconcile_succession_transition_v1,
)


def _component(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def _bundle(
    *,
    character_id: int,
    snapshot_id: str,
    revision: int,
    native_revision: int,
    date_raw: int,
    title_rows: list[dict[str, object]],
    primary_heir: int | None,
) -> dict[str, object]:
    heir = (
        _component(primary_heir)
        if primary_heir is not None
        else {
            "status": "not_applicable",
            "value": None,
            "unavailable_reason": "no_observed_primary_title_successor",
        }
    )
    return {
        "schema": "xar.ck3.turn-bundle/v1",
        "status": "available",
        "binding": {
            "snapshot_id": snapshot_id,
            "revision": revision,
            "native_revision": native_revision,
            "date_raw": date_raw,
        },
        "ruler_state": _component(
            {"character_id": character_id, "alive": True}
        ),
        "succession_state": _component(
            {
                "primary_title_heir_character_id": heir,
                "partition": _component(
                    {
                        "title_heirs": title_rows,
                        "risk_state": (
                            "no_primary_heir"
                            if primary_heir is None
                            else "split_successors"
                        ),
                    }
                ),
            }
        ),
    }


def _row(title_id: int, heir_id: int | None, *, primary: bool) -> dict[str, object]:
    return {
        "title": {"title_id": title_id, "tier_raw": 4 if primary else 2, "tier_key": "kingdom" if primary else "county"},
        "first_heir_character_id": heir_id,
        "primary": primary,
    }


class SuccessionTransitionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pre = _bundle(
            character_id=100,
            snapshot_id="native:20",
            revision=7,
            native_revision=20,
            date_raw=53_180_000,
            title_rows=[
                _row(10, 200, primary=True),
                _row(11, 200, primary=False),
                _row(12, 300, primary=False),
                _row(13, None, primary=False),
            ],
            primary_heir=200,
        )
        self.post = _bundle(
            character_id=200,
            snapshot_id="native:24",
            revision=8,
            native_revision=24,
            date_raw=53_180_720,
            title_rows=[
                _row(10, 400, primary=True),
                _row(11, 400, primary=False),
                _row(99, 400, primary=False),
            ],
            primary_heir=400,
        )
        self.snapshot = {
            "snapshot_id": "native:24",
            "revision": 8,
            "native_revision": 24,
            "date_raw": 53_180_720,
            "paused": True,
            "played_character": {"character_id": 200, "alive": True},
            "episode_character_id": 100,
            "one_life_terminal": True,
            "one_life_terminal_reason": "played_character_changed",
        }

    def test_freezes_exact_per_title_expectation(self) -> None:
        result = freeze_succession_expectation_v1(
            self.pre,
            episode_run_id="native-100-test",
            episode_character_id=100,
        )

        self.assertEqual(result["schema"], SUCCESSION_EXPECTATION_V1_SCHEMA)
        self.assertEqual(result["expectation_state"], "successor_expected")
        self.assertEqual(result["expected_successor_character_id"], 200)
        self.assertEqual(result["binding"]["native_revision"], 20)
        self.assertEqual(
            [row["title"]["title_id"] for row in result["title_expectations"]],
            [10, 11, 12, 13],
        )

    def test_reconciles_only_titles_owned_by_the_predecessor(self) -> None:
        expectation = freeze_succession_expectation_v1(
            self.pre,
            episode_run_id="native-100-test",
            episode_character_id=100,
        )

        result = reconcile_succession_transition_v1(
            expectation, self.snapshot, self.post
        )

        self.assertEqual(result["schema"], SUCCESSION_RECONCILIATION_V1_SCHEMA)
        self.assertEqual(result["verdict"], "matched")
        self.assertTrue(result["successor_match"])
        self.assertTrue(result["title_distribution_match"])
        self.assertEqual(result["matched_inherited_title_ids"], [10, 11])
        self.assertEqual(result["expected_other_heir_title_ids"], [12])
        self.assertEqual(result["expected_without_heir_title_ids"], [13])
        self.assertEqual(result["observed_additional_successor_title_ids"], [99])

    def test_reports_successor_and_title_mismatches_without_inventing_holders(self) -> None:
        expectation = freeze_succession_expectation_v1(
            self.pre,
            episode_run_id="native-100-test",
            episode_character_id=100,
        )
        wrong_successor = copy.deepcopy(self.snapshot)
        wrong_successor["played_character"]["character_id"] = 201
        wrong_post = copy.deepcopy(self.post)
        wrong_post["ruler_state"]["value"]["character_id"] = 201
        wrong_post["succession_state"]["value"]["partition"]["value"]["title_heirs"] = [
            _row(10, 400, primary=True),
            _row(12, 400, primary=False),
        ]

        result = reconcile_succession_transition_v1(
            expectation, wrong_successor, wrong_post
        )

        self.assertEqual(result["verdict"], "unexpected_successor")
        self.assertFalse(result["successor_match"])
        self.assertFalse(result["title_distribution_match"])
        self.assertEqual(result["missing_expected_inherited_title_ids"], [11])
        self.assertEqual(
            result["unexpected_retained_predecessor_title_ids"], [12]
        )

    def test_freezes_no_heir_as_observed_risk(self) -> None:
        no_heir = _bundle(
            character_id=100,
            snapshot_id="native:20",
            revision=7,
            native_revision=20,
            date_raw=53_180_000,
            title_rows=[_row(10, None, primary=True)],
            primary_heir=None,
        )

        result = freeze_succession_expectation_v1(
            no_heir,
            episode_run_id="native-100-test",
            episode_character_id=100,
        )

        self.assertEqual(result["expectation_state"], "no_primary_heir")
        self.assertIsNone(result["expected_successor_character_id"])

    def test_rejects_cross_frame_and_non_transition_inputs(self) -> None:
        expectation = freeze_succession_expectation_v1(
            self.pre,
            episode_run_id="native-100-test",
            episode_character_id=100,
        )
        drifted = copy.deepcopy(self.post)
        drifted["binding"]["native_revision"] += 1
        active = copy.deepcopy(self.snapshot)
        active["one_life_terminal_reason"] = None

        with self.assertRaises(ValueError):
            reconcile_succession_transition_v1(
                expectation, self.snapshot, drifted
            )
        with self.assertRaises(ValueError):
            reconcile_succession_transition_v1(expectation, active, self.post)


if __name__ == "__main__":
    unittest.main()
