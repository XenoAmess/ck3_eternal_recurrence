from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.war_cash_floor_policy_provenance_v1 import (
    SCHEMA, assess_war_cash_floor_policy_candidate_v1,
)


WAR_ID = 16777231
FRAME = {
    "played_character_id": 29829, "native_revision": 3,
    "date_raw": 53217624, "snapshot_id": "native:3", "revision": 4,
    "episode_run_id": "native-29829-2bc2d599f7f9",
}


def policy(**changes: object) -> bytes:
    row = {
        "schema": SCHEMA, "policy_id": "synthetic-war-floor-test",
        "policy_version": "test-v1", "played_character_id": 29829,
        "episode_run_id": FRAME["episode_run_id"], "war_id": WAR_ID,
        "valid_from_date_raw": 53217620,
        "valid_until_date_raw": FRAME["date_raw"] + 24,
        "valid_through_horizon_days": 1,
        "floor_raw": 25_000_000, "gold_scale": 100_000,
        "floor_purpose": "terminal_liquidity_after_horizon",
        "floor_claim_ids": ["war:16777231:terminal-liquidity"],
        "amount_basis": "synthetic test policy, not a Robert decision",
        "reviewer_evidence_sha256": "A" * 64,
    }
    row.update(changes)
    return json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8")


def assess(data: bytes | None, **changes: object) -> dict[str, object]:
    args: dict[str, object] = {
        "frame": FRAME, "war_id": WAR_ID, "horizon_days": 1,
        "policy_document_bytes": data,
        "pinned_policy_sha256": (
            hashlib.sha256(data).hexdigest().upper() if data is not None else None
        ),
        "future_spend_claim_ids": ["war:16777231:upkeep-day-1"],
        "risk_spend_claim_ids": ["war:16777231:risk-day-1"],
    }
    args.update(changes)
    return assess_war_cash_floor_policy_candidate_v1(**args)


class WarCashFloorPolicyProvenanceTests(unittest.TestCase):
    def test_missing_published_policy_stays_unknown(self) -> None:
        seen = assess(None)
        self.assertEqual(seen["status"], "policy_source_unavailable_unknown")
        self.assertIsNone(seen["candidate_policy_floor_raw"])
        self.assertFalse(seen["formal_cash_receipt_eligible"])

    def test_incomplete_frame_fails_before_policy_lookup(self) -> None:
        with self.assertRaisesRegex(ValueError, "observed frame identity"):
            assess(None, frame={**FRAME, "native_revision": None})

    def test_synthetic_explicit_floor_is_only_a_candidate(self) -> None:
        seen = assess(policy())
        self.assertEqual(seen["status"], "candidate_document_and_claims_valid")
        self.assertEqual(seen["candidate_policy_floor_raw"], 25_000_000)
        self.assertEqual(seen["policy_version"], "test-v1")
        self.assertFalse(seen["formal_cash_receipt_eligible"])

    def test_pin_and_scope_changes_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "differ from reviewed pin"):
            assess(policy(), pinned_policy_sha256="B" * 64)
        for change in (
            {"played_character_id": 100},
            {"war_id": WAR_ID + 1},
            {"episode_run_id": "other-run"},
            {"valid_until_date_raw": FRAME["date_raw"] - 1},
            {"valid_until_date_raw": FRAME["date_raw"] + 1},
            {"valid_through_horizon_days": 0},
            {"floor_purpose": "future_expense"},
        ):
            with self.subTest(change=change), self.assertRaisesRegex(
                ValueError, "stale, foreign or lacks reviewed basis"
            ):
                assess(policy(**change))

    def test_duplicated_uses_reject_additive_reserve(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate a cash use"):
            assess(policy(floor_claim_ids=["war:16777231:risk-day-1"]))
        with self.assertRaisesRegex(ValueError, "duplicate a cash use"):
            assess(policy(), risk_spend_claim_ids=["war:16777231:upkeep-day-1"])

    def test_missing_risk_scope_and_duplicate_json_keys_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "risk spend needs"):
            assess(policy(), risk_spend_claim_ids=None)
        data = policy().replace(b'"floor_raw": 25000000',
                                b'"floor_raw": 25000000, "floor_raw": 1')
        with self.assertRaisesRegex(ValueError, "repeats a JSON key"):
            assess(data)

    def test_explicit_zero_does_not_prove_h3686_policy(self) -> None:
        seen = assess(policy(floor_raw=0))
        self.assertEqual(seen["candidate_policy_floor_raw"], 0)
        self.assertFalse(seen["formal_cash_receipt_eligible"])


if __name__ == "__main__":
    unittest.main()
