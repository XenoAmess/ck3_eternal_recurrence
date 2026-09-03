#!/usr/bin/env python3
"""Focused tests for review-gated Phase2 authoring promotion."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import promote_phase2_reviewed_authoring as promotion


PROMO = promotion.REPOSITORY_ROOT / "mod_zhongguo_style" / "promo"


class ReviewedAuthoringPromotionTests(unittest.TestCase):
    def _inputs(self, root: Path):
        project = PROMO / "phase2-promo-character-project.json"
        ledger = PROMO / "phase2-authoring-character-claims.json"
        intake = root / "footage-intake.json"
        intake.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "zg361_phase2_footage_intake",
                    "result": "GREEN",
                    "reason_code": None,
                }
            ),
            encoding="utf-8",
        )
        materialized_errors: list[str] = []
        materialized = promotion.materialize_ledger(ledger, materialized_errors)
        self.assertEqual([], materialized_errors)
        cue_ids = [row["cue"]["id"] for row in materialized["chapters"]]
        review = root / "source-review.json"
        review.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": promotion.SOURCE_REVIEW_KIND,
                    "result": "GREEN",
                    "decision": "approved",
                    "cut_id": "character-led",
                    "playback_speed": 1,
                    "full_duration_reviewed": True,
                    "reviewer": "Reviewer A",
                    "reviewed_at": "2026-09-03T12:00:00+08:00",
                    "all_claims_supported": True,
                    "approved_cue_ids": cue_ids,
                    "template_only": False,
                    "is_signoff": True,
                    "project_config": promotion._record(project),
                    "authoring_ledger": promotion._record(ledger),
                    "footage_intake": promotion._record(intake),
                }
            ),
            encoding="utf-8",
        )
        return project, ledger, intake, review

    def test_reviewed_receipt_projects_ten_ready_cues(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project, ledger, intake, review = self._inputs(Path(raw))
            promoted, audit = promotion.build_promoted_project(
                project_config=project,
                authoring_ledger=ledger,
                footage_intake_report=intake,
                source_review_receipt=review,
            )
            self.assertEqual("GREEN", audit["result"])
            self.assertEqual(10, audit["chapters_promoted"])
            chapters = promoted["chapters"]
            self.assertTrue(all(row["state"] == "ready" for row in chapters))
            self.assertTrue(all(len(row["cues"]) == 1 for row in chapters))
            self.assertTrue(
                all(
                    row["artifact_ids"]
                    == [
                        "narration."
                        + promotion._segment_id(row["id"], row["cues"][0]["id"])
                    ]
                    for row in chapters
                )
            )

    def test_validate_only_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project, ledger, intake, review = self._inputs(root)
            attempt = root / "must-not-exist"
            output_project = attempt / project.name
            output_receipt = attempt / "promotion.json"
            with contextlib.redirect_stdout(io.StringIO()):
                result = promotion.main(
                    (
                        "--project-config",
                        str(project),
                        "--authoring-ledger",
                        str(ledger),
                        "--footage-intake-report",
                        str(intake),
                        "--source-review-receipt",
                        str(review),
                        "--output-project",
                        str(output_project),
                        "--output-receipt",
                        str(output_receipt),
                        "--validate-only",
                    )
                )
            self.assertEqual(0, result)
            self.assertFalse(attempt.exists())

    def test_template_or_unapproved_receipt_cannot_promote(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project, ledger, intake, review = self._inputs(root)
            payload = json.loads(review.read_text(encoding="utf-8"))
            payload["decision"] = "pending"
            review.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(promotion.PromotionError, "explicit GREEN approval"):
                promotion.build_promoted_project(
                    project_config=project,
                    authoring_ledger=ledger,
                    footage_intake_report=intake,
                    source_review_receipt=review,
                )


if __name__ == "__main__":
    unittest.main()
