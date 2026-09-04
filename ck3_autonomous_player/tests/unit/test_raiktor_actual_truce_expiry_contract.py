from __future__ import annotations

import unittest

from xar_autoplayer.bridge.raiktor_actual_truce_expiry_contract import (
    RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_BACKEND_ID,
    normalize_raiktor_actual_truce_expiry_v1,
    parse_query_raiktor_actual_truce_expiry_v1_step,
)


STEP = "query-raiktor-actual-truce-expiry-v1-33554442"


def result(*, status: str = "available") -> dict[str, object]:
    available = status == "available"
    return {
        "step": STEP,
        "accepted": True,
        "query_sequence": 1,
        "snapshot_revision": 9,
        "raiktor_actual_truce_expiry": {
            "schema_version": 1,
            "backend_id": RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_BACKEND_ID,
            "status": status,
            "snapshot_revision": 9,
            "current_date_raw": 1000,
            "owner_character_id": 16777217,
            "toward_character_id": 33554442,
            "native_has_truce": available,
            "actual_expiry_observable": available,
            "expiry_date_raw": 44800 if available else None,
            "same_frame_stable": True,
            "readiness": available,
            "temporal_semantics": "post_application_persisted_relation_state",
            "unavailable_reason": None if available else "native_has_truce_false",
        },
        "backend_id": "native-headless",
    }


class RaiktorActualTruceExpiryContractTests(unittest.TestCase):
    def test_canonical_generation_safe_step(self) -> None:
        self.assertEqual(
            parse_query_raiktor_actual_truce_expiry_v1_step(STEP), 33554442
        )
        for invalid in (
            "query-raiktor-actual-truce-expiry-v1-0",
            "query-raiktor-actual-truce-expiry-v1-01",
            "query-raiktor-actual-truce-expiry-v1--1",
            "query-raiktor-actual-truce-expiry-v1-N",
        ):
            self.assertIsNone(
                parse_query_raiktor_actual_truce_expiry_v1_step(invalid)
            )

    def test_available_requires_provider_observed_future_expiry(self) -> None:
        normalized = normalize_raiktor_actual_truce_expiry_v1(
            result(), expected_step=STEP, expected_snapshot_revision=9
        )
        self.assertTrue(normalized["readiness"])
        self.assertEqual(normalized["expiry_date_raw"], 44800)

    def test_ack_cannot_turn_absence_green(self) -> None:
        normalized = normalize_raiktor_actual_truce_expiry_v1(
            result(status="no_truce"),
            expected_step=STEP,
            expected_snapshot_revision=9,
        )
        self.assertFalse(normalized["readiness"])
        self.assertIsNone(normalized["expiry_date_raw"])

    def test_rejects_ack_with_fabricated_readiness(self) -> None:
        malformed = result(status="no_truce")
        payload = malformed["raiktor_actual_truce_expiry"]
        assert isinstance(payload, dict)
        payload["readiness"] = True
        with self.assertRaisesRegex(ValueError, "no-truce"):
            normalize_raiktor_actual_truce_expiry_v1(
                malformed, expected_step=STEP, expected_snapshot_revision=9
            )


if __name__ == "__main__":
    unittest.main()
