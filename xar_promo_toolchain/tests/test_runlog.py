from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from xar_promo.model import RunManifest
from xar_promo.operations import initialize_project, preserve_artifact
from xar_promo.project import load_document
from xar_promo.runlog import (
    ArtifactReference,
    AutomatedAuditRecord,
    PhaseRecord,
    RunLogError,
    append_automated_audit_record,
    append_phase_record,
    automated_audit_records_from_run,
    phase_records_from_run,
)


class RunLogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "project"
        _, self.run_path = initialize_project(
            self.root,
            project_id="runlog-test",
            title="Runlog Test",
            narration_locale="und",
            subtitle_locales=["und"],
            adapter="generic",
            preset="default",
            run_id="run-0001",
        )
        self.records = {}
        for artifact_id, role, payload in (
            ("phase-plan", "plan", b"phase plan"),
            ("phase-log", "log", b"phase log"),
            ("subject-video", "deliverable", b"subject bytes"),
            ("audit-report", "audit-report", b"audit report bytes"),
        ):
            source = Path(self.temporary.name) / f"{artifact_id}.bin"
            source.write_bytes(payload)
            self.records[artifact_id] = preserve_artifact(
                self.run_path,
                source,
                artifact_id=artifact_id,
                collection="derived",
                role=role,
                label=artifact_id,
                media_type="application/octet-stream",
            )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _history_count(self) -> int:
        return len(
            list(
                (self.run_path.parent / "artifacts" / "manifest-history").rglob(
                    "*.json"
                )
            )
        )

    def test_phase_append_is_typed_gap_free_and_archives_each_previous_manifest(self) -> None:
        before = self._history_count()
        first = append_phase_record(
            self.run_path,
            phase_id="draft-validate",
            status="succeeded",
            artifact_ids=(),
            detail="validated without producing an artifact",
            recorded_at="2026-09-01T00:00:00+00:00",
        )
        second = append_phase_record(
            self.run_path,
            phase_id="segment-plan",
            status="failed",
            artifact_ids=("phase-plan", "phase-log"),
            recorded_at="2026-09-01T00:01:00Z",
        )
        self.assertEqual("phase-000001", first.record_id)
        self.assertEqual("2026-09-01T00:00:00Z", first.recorded_at)
        self.assertEqual((), first.artifacts)
        self.assertEqual("phase-000002", second.record_id)
        self.assertEqual(
            ["phase-plan", "phase-log"],
            [item.artifact_id for item in second.artifacts],
        )
        loaded = load_document(self.run_path).run
        self.assertIsNotNone(loaded)
        records = phase_records_from_run(loaded)
        self.assertEqual([1, 2], [record.sequence for record in records])
        self.assertEqual(before + 2, self._history_count())

    def test_pure_projection_does_not_mutate_the_run(self) -> None:
        before = self.run_path.read_bytes()
        record = PhaseRecord.create(
            sequence=1,
            phase_id="render",
            status="succeeded",
            recorded_at="2026-09-01T00:00:00Z",
            artifacts=[self.records["phase-plan"]],
        )
        self.assertEqual("phase-plan", record.artifacts[0].artifact_id)
        self.assertEqual(before, self.run_path.read_bytes())

    def test_automated_audit_binds_subject_and_report_but_never_signs_off(self) -> None:
        before = self._history_count()
        record = append_automated_audit_record(
            self.run_path,
            check_id="media-integrity",
            status="passed",
            subject_artifact_id="subject-video",
            report_artifact_id="audit-report",
            recorded_at="2026-09-01T00:02:00Z",
        )
        self.assertEqual("audit-000001", record.record_id)
        self.assertEqual("subject-video", record.subject.artifact_id)
        self.assertEqual("audit-report", record.report.artifact_id)
        loaded = load_document(self.run_path).run
        self.assertIsNotNone(loaded)
        self.assertEqual((), loaded.signoffs)
        self.assertEqual((record,), automated_audit_records_from_run(loaded))
        self.assertEqual(before + 1, self._history_count())

        unchanged = self.run_path.read_bytes()
        with self.assertRaisesRegex(RunLogError, "must be one of"):
            append_automated_audit_record(
                self.run_path,
                check_id="media-integrity",
                status="approved",
                subject_artifact_id="subject-video",
                report_artifact_id="audit-report",
                recorded_at="2026-09-01T00:03:00Z",
            )
        self.assertEqual(unchanged, self.run_path.read_bytes())

    def test_non_utc_or_missing_artifacts_fail_before_mutation(self) -> None:
        before = self.run_path.read_bytes()
        with self.assertRaisesRegex(RunLogError, "must use UTC"):
            append_phase_record(
                self.run_path,
                phase_id="capture",
                status="started",
                recorded_at="2026-09-01T08:00:00+08:00",
            )
        self.assertEqual(before, self.run_path.read_bytes())
        with self.assertRaisesRegex(RunLogError, "missing artifacts"):
            append_phase_record(
                self.run_path,
                phase_id="capture",
                status="failed",
                artifact_ids=["missing-log"],
                recorded_at="2026-09-01T00:00:00Z",
            )
        self.assertEqual(before, self.run_path.read_bytes())

    def test_typed_readers_reject_sequence_and_hash_tampering(self) -> None:
        run = load_document(self.run_path).run
        self.assertIsNotNone(run)
        source = self.records["phase-plan"]
        gap = PhaseRecord.create(
            sequence=2,
            phase_id="plan",
            status="succeeded",
            recorded_at="2026-09-01T00:00:00Z",
            artifacts=[source],
        )
        with self.assertRaisesRegex(RunLogError, "gap-free"):
            phase_records_from_run(replace(run, phase_history=(gap.to_dict(),)))

        wrong_subject = ArtifactReference(
            source.artifact_id,
            source.bytes,
            "0" * 64,
        )
        audit = AutomatedAuditRecord.create(
            sequence=1,
            check_id="hash-check",
            status="failed",
            recorded_at="2026-09-01T00:00:00Z",
            subject=wrong_subject,
            report=self.records["audit-report"],
        )
        with self.assertRaisesRegex(RunLogError, "does not match"):
            automated_audit_records_from_run(replace(run, audits=(audit.to_dict(),)))


if __name__ == "__main__":
    unittest.main()
