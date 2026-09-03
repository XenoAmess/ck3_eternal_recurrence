#!/usr/bin/env python3

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from zhongguo_phase2_business_postconditions import (  # noqa: E402
    ENDGAME_HANDLER,
    PROJECTS_HANDLER,
    PROMOTION_HANDLER,
    SCOREBOARD_HANDLER,
    verify_phase2_business_postcondition,
)


FIXTURE = TOOLS / "fixtures" / "phase2_business_postconditions_v1.json"


def _cases() -> dict[str, dict[str, object]]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    return payload["cases"]


class Phase2BusinessPostconditionTests(unittest.TestCase):
    def test_all_canonical_fixtures_are_green(self) -> None:
        cases = _cases()
        self.assertEqual(
            set(cases),
            {SCOREBOARD_HANDLER, PROMOTION_HANDLER, PROJECTS_HANDLER, ENDGAME_HANDLER},
        )
        for handler, evidence in cases.items():
            with self.subTest(handler=handler):
                result = verify_phase2_business_postcondition(handler, evidence)
                self.assertEqual(result["result"], "GREEN")
                self.assertTrue(result["provider_observed"])
                self.assertTrue(result["postcondition_green"])
                self.assertIsNone(result["reason_code"])

    def test_ack_only_is_red_even_when_all_revisions_advance(self) -> None:
        for handler, original in _cases().items():
            with self.subTest(handler=handler):
                evidence = deepcopy(original)
                evidence["observation"]["action_ack_only"] = True
                result = verify_phase2_business_postcondition(handler, evidence)
                self.assertEqual(result["result"], "RED")
                self.assertFalse(result["postcondition_green"])
                self.assertEqual(result["reason_code"], "not_ack_only")
                if handler != SCOREBOARD_HANDLER:
                    self.assertTrue(result["checks"]["revision_advanced"])
                    self.assertTrue(result["checks"]["native_revision_advanced"])

    def test_revision_advance_without_provider_observation_is_red(self) -> None:
        for handler, original in _cases().items():
            with self.subTest(handler=handler):
                evidence = deepcopy(original)
                evidence["observation"]["provider_observed"] = False
                result = verify_phase2_business_postcondition(handler, evidence)
                self.assertEqual(result["result"], "RED")
                self.assertEqual(result["reason_code"], "provider_observed")
                if handler != SCOREBOARD_HANDLER:
                    self.assertTrue(result["checks"]["revision_advanced"])

    def test_scoreboard_requires_visible_identity_ready_calibration_event(self) -> None:
        evidence = deepcopy(_cases()[SCOREBOARD_HANDLER])
        evidence["calibration_event"]["visible"] = False
        result = verify_phase2_business_postcondition(SCOREBOARD_HANDLER, evidence)
        self.assertEqual(result["result"], "RED")
        self.assertFalse(
            result["checks"]["calibration_event_visible_and_identity_ready"]
        )

        evidence = deepcopy(_cases()[SCOREBOARD_HANDLER])
        evidence["calibration_event"]["definition_key"] = "zg361b1.201"
        result = verify_phase2_business_postcondition(SCOREBOARD_HANDLER, evidence)
        self.assertEqual(result["result"], "RED")

    def test_scoreboard_requires_semantic_change_not_only_public_revision(self) -> None:
        evidence = deepcopy(_cases()[SCOREBOARD_HANDLER])
        evidence["scoreboard_after"]["observed_state_revision"] = evidence[
            "scoreboard_before"
        ]["observed_state_revision"]
        evidence["scoreboard_after"]["semantic_fingerprint"] = evidence[
            "scoreboard_before"
        ]["semantic_fingerprint"]
        result = verify_phase2_business_postcondition(SCOREBOARD_HANDLER, evidence)
        self.assertEqual(result["result"], "RED")
        self.assertFalse(result["checks"]["scoreboard_observation_revision_advanced"])
        self.assertFalse(result["checks"]["scoreboard_semantic_fingerprint_changed"])

    def test_promotion_rejects_cross_case_compensation_receipt(self) -> None:
        evidence = deepcopy(_cases()[PROMOTION_HANDLER])
        evidence["compensation_receipt"]["identity"]["case_serial"] += 1
        result = verify_phase2_business_postcondition(PROMOTION_HANDLER, evidence)
        self.assertEqual(result["result"], "RED")
        self.assertFalse(result["checks"]["same_frozen_case_identity"])

    def test_promotion_requires_posted_provider_receipt(self) -> None:
        evidence = deepcopy(_cases()[PROMOTION_HANDLER])
        evidence["compensation_receipt"]["posted"] = False
        result = verify_phase2_business_postcondition(PROMOTION_HANDLER, evidence)
        self.assertEqual(result["result"], "RED")
        self.assertFalse(result["checks"]["compensation_receipt_posted"])

    def test_projects_rejects_cross_case_or_unlinked_metrics(self) -> None:
        evidence = deepcopy(_cases()[PROJECTS_HANDLER])
        evidence["metrics_result"]["identity"]["case_serial"] += 1
        result = verify_phase2_business_postcondition(PROJECTS_HANDLER, evidence)
        self.assertEqual(result["result"], "RED")
        self.assertFalse(result["checks"]["same_project_case_identity"])

        evidence = deepcopy(_cases()[PROJECTS_HANDLER])
        evidence["metrics_result"]["source_contribution_receipt_id"] += 1
        result = verify_phase2_business_postcondition(PROJECTS_HANDLER, evidence)
        self.assertEqual(result["result"], "RED")
        self.assertFalse(result["checks"]["contribution_metrics_receipt_identity"])

    def test_endgame_requires_carried_debt_and_next_cycle_default(self) -> None:
        evidence = deepcopy(_cases()[ENDGAME_HANDLER])
        evidence["carried_debt"]["carried_into_cycle_serial"] += 1
        result = verify_phase2_business_postcondition(ENDGAME_HANDLER, evidence)
        self.assertEqual(result["result"], "RED")
        self.assertFalse(result["checks"]["debt_carried_into_terminal_cycle"])

        evidence = deepcopy(_cases()[ENDGAME_HANDLER])
        evidence["default_change"]["effective_cycle_serial"] += 1
        result = verify_phase2_business_postcondition(ENDGAME_HANDLER, evidence)
        self.assertEqual(result["result"], "RED")
        self.assertFalse(result["checks"]["default_changes_next_cycle"])

    def test_event_surface_must_be_bound_to_provider_frame(self) -> None:
        for handler in (PROMOTION_HANDLER, PROJECTS_HANDLER, ENDGAME_HANDLER):
            with self.subTest(handler=handler):
                evidence = deepcopy(_cases()[handler])
                evidence["result_event"]["snapshot_revision"] += 1
                result = verify_phase2_business_postcondition(handler, evidence)
                self.assertEqual(result["result"], "RED")
                self.assertFalse(result["checks"]["events_bound_to_observation_frames"])

    def test_exact_packet_shape_and_scalar_types_are_required(self) -> None:
        evidence = deepcopy(_cases()[PROMOTION_HANDLER])
        evidence["unexpected"] = "ignored only by an unsafe verifier"
        result = verify_phase2_business_postcondition(PROMOTION_HANDLER, evidence)
        self.assertEqual(result["result"], "RED")
        self.assertEqual(result["reason_code"], "schema_version")

        evidence = deepcopy(_cases()[PROMOTION_HANDLER])
        evidence["promotion_choice"]["receipt_serial"] = True
        result = verify_phase2_business_postcondition(PROMOTION_HANDLER, evidence)
        self.assertEqual(result["result"], "RED")
        self.assertFalse(result["checks"]["promotion_choice_receipt_observed"])

    def test_unknown_handler_is_typed_red(self) -> None:
        result = verify_phase2_business_postcondition("unknown", {})
        self.assertEqual(result["result"], "RED")
        self.assertEqual(result["reason_code"], "supported_handler")


if __name__ == "__main__":
    unittest.main()
