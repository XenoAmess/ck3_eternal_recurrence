"""Focused no-launch checks of real-row selection and helper-free rejection."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

import council_four_gate_reject_v1 as subject


def scene(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "position_key": "councillor_steward",
        "native_helper_invocations_delta": 0,
        "public_registered_or_advertised": False,
        "owner_character_id": 29829,
        "incumbent_character_id": 33433,
        "vacant": False,
        "candidate_count": 11,
        "snapshot": {"paused": True, "date_raw": 53178264,
                     "native_revision": 3, "public_revision": 3,
                     "snapshot_id": "native:3"},
        "isolated_guest_rejection_ids": [],
        "isolated_candidate_pending_rejection_ids": [],
        "isolated_replacement_fireability_denial_ids": [],
    }
    result.update(overrides)
    return result


class CouncilFourGateRejectTests(unittest.TestCase):
    def test_historically_missing_positive_scenes_cannot_produce_an_id(self) -> None:
        with patch.object(subject, "inspect", return_value=scene()):
            for gate in subject.GATES:
                with self.subTest(gate=gate):
                    with self.assertRaises(subject.PositiveSceneMissing):
                        subject.select(Path("frozen-query.json"), "A" * 64, gate)

    def test_each_gate_selects_only_its_isolated_native_provider_row(self) -> None:
        fields = {
            "guest": "isolated_guest_rejection_ids",
            "candidate_pending": "isolated_candidate_pending_rejection_ids",
            "replacement_fireability_denial":
                "isolated_replacement_fireability_denial_ids",
        }
        for gate, field in fields.items():
            with self.subTest(gate=gate):
                with patch.object(subject, "inspect", return_value=scene(
                        **{field: [30784, 33433]})):
                    plan = subject.select(Path("frozen-query.json"), "A" * 64, gate)
                    self.assertEqual(plan["candidate_character_id"], 30784)
                    self.assertEqual(plan["expected_failure"],
                                     subject.GATES[gate][1])
                    self.assertFalse(plan["public_registered_or_advertised"])

    def test_reject_requires_typed_failure_without_native_helper(self) -> None:
        plan = {"gate": "candidate_pending",
                "expected_failure": "pending_character_interaction"}
        valid = {"status": "rejected_before_submit",
                 "failure": "pending_character_interaction",
                 "native_helper_invoked": False,
                 "verification_pending": False,
                 "queue_acceptance_observed": False}
        subject.validate_rejection_ack(valid, plan)
        for altered in ({**valid, "native_helper_invoked": True},
                        {**valid, "failure": "candidate_is_guest"},
                        {**valid, "queue_acceptance_observed": True}):
            with self.assertRaises(ValueError):
                subject.validate_rejection_ack(altered, plan)


if __name__ == "__main__":
    unittest.main()
