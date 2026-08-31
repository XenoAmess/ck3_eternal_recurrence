from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from xar_promo.audit import AuditError, verify_audit_report, write_audit_report
from xar_promo.evidence import (
    EvidenceError,
    bind_external_artifact,
    build_sampling_plan,
    deterministic_timestamps,
    load_evidence_bundle,
    make_source_record,
    write_evidence_bundle,
    write_sampling_plan,
)
from xar_promo.operations import initialize_project, preserve_artifact, record_signoff


class AuditEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        project = Path(self.temporary.name) / "sample"
        _, self.run_path = initialize_project(
            project,
            project_id="sample",
            title="Sample",
            narration_locale="zh-CN",
            subtitle_locales=["zh-CN", "en"],
            adapter="generic",
            preset="default",
            run_id="run-0001",
        )
        self.root = self.run_path.parent
        self.capture = self.root / "artifacts" / "raw" / "capture.mp4"
        self.capture.parent.mkdir(parents=True, exist_ok=True)
        self.capture.write_bytes(b"fake captured video bytes")
        self.frame_producer = {
            "adapter_id": "generic-media",
            "tool": "ffmpeg",
            "tool_version": "test-version",
            "operation": "extract-frame",
            "execution": "external",
        }
        self.ocr_producer = {
            "adapter_id": "generic-ocr",
            "tool": "tesseract",
            "tool_version": "test-version",
            "operation": "ocr-frame",
            "execution": "external",
        }
        capture_producer = {
            "adapter_id": "generic-capture",
            "tool": "screen-recorder",
            "tool_version": "test-version",
            "operation": "capture",
            "execution": "external",
        }
        self.source = bind_external_artifact(
            self.capture,
            project_root=self.root,
            artifact_id="capture-001",
            collection="raw",
            role="capture",
            label="Captured source",
            media_type="video/mp4",
            producer=capture_producer,
        )
        self.chapters = [
            {
                "id": "chapter-b",
                "kind": "video",
                "source": self.source,
                "start_seconds": 1,
                "end_seconds": 2,
            },
            {
                "id": "chapter-a",
                "kind": "video",
                "source": self.source,
                "start_seconds": 0,
                "end_seconds": 2,
            },
        ]

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_plan(self) -> tuple[Path, dict]:
        path = self.root / "artifacts" / "derived" / "evidence-plan.json"
        plan = write_sampling_plan(
            path,
            self.chapters,
            project_root=self.root,
            interval_seconds=1,
            frame_producer=self.frame_producer,
            ocr_producer=self.ocr_producer,
        )
        return path, plan

    def _submissions(self, plan: dict) -> list[dict]:
        submissions = []
        for sample in plan["samples"]:
            for role, producer, media_type in (
                ("frame", self.frame_producer, "image/png"),
                ("ocr", self.ocr_producer, "application/json"),
            ):
                path = self.root / "artifacts" / "derived" / "evidence" / f"{sample['id']}-{role}.bin"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(f"{sample['id']}:{role}".encode("ascii"))
                submissions.append(
                    {
                        "sample_id": sample["id"],
                        "role": role,
                        "path": path,
                        "media_type": media_type,
                        "producer": producer,
                    }
                )
        return submissions

    def _write_complete_bundle(self) -> tuple[Path, dict, list[dict]]:
        plan_path, plan = self._write_plan()
        submissions = self._submissions(plan)
        bundle_path = self.root / "artifacts" / "derived" / "evidence-bundle.json"
        write_evidence_bundle(
            bundle_path,
            project_root=self.root,
            plan_path=plan_path,
            submissions=submissions,
        )
        return bundle_path, plan, submissions

    def _subject(self):
        final_source = Path(self.temporary.name) / "final.mp4"
        final_source.write_bytes(b"fake final promotional video")
        return preserve_artifact(
            self.run_path,
            final_source,
            artifact_id="final-video",
            collection="derived",
            role="deliverable",
            label="Final video",
            media_type="video/mp4",
        )

    def test_sampling_is_deterministic_and_deduplicates_overlap(self) -> None:
        self.assertEqual(
            ["0.000000", "1.000000", "2.000000", "2.250000"],
            deterministic_timestamps(0, 2.25, 1),
        )
        first = build_sampling_plan(
            self.chapters,
            project_root=self.root,
            interval_seconds=1,
            frame_producer=self.frame_producer,
            ocr_producer=self.ocr_producer,
        )
        second = build_sampling_plan(
            reversed(self.chapters),
            project_root=self.root,
            interval_seconds="1.000000",
            frame_producer=self.frame_producer,
            ocr_producer=self.ocr_producer,
        )
        self.assertEqual(first, second)
        self.assertEqual(3, len(first["samples"]))
        overlapping = next(item for item in first["samples"] if item["timestamp_seconds"] == "1.000000")
        self.assertEqual(["chapter-a", "chapter-b"], overlapping["chapter_ids"])

    def test_missing_evidence_fails_closed_before_bundle_is_written(self) -> None:
        plan_path, plan = self._write_plan()
        submissions = self._submissions(plan)[:-1]
        bundle_path = self.root / "artifacts" / "derived" / "incomplete-bundle.json"
        with self.assertRaisesRegex(EvidenceError, "required evidence is missing"):
            write_evidence_bundle(
                bundle_path,
                project_root=self.root,
                plan_path=plan_path,
                submissions=submissions,
            )
        self.assertFalse(bundle_path.exists())

    def test_complete_bundle_reverifies_every_hash_binding(self) -> None:
        bundle_path, plan, _ = self._write_complete_bundle()
        bundle, loaded_plan = load_evidence_bundle(bundle_path, project_root=self.root)
        self.assertEqual(plan, loaded_plan)
        self.assertEqual(len(plan["samples"]) * 2, len(bundle["entries"]))

    def test_report_is_append_only_and_does_not_auto_approve(self) -> None:
        bundle_path, _, _ = self._write_complete_bundle()
        subject = self._subject()
        report_path = self.root / "artifacts" / "derived" / "audit-report.json"
        report = write_audit_report(
            report_path,
            project_root=self.root,
            subject=subject,
            evidence_bundle_path=bundle_path,
            created_at_utc="2026-09-01T00:00:00Z",
        )
        self.assertEqual("passed", report["automated_audit"]["status"])
        self.assertFalse(report["automated_audit"]["manual_approval_granted"])
        self.assertEqual({"state": "not-provided"}, report["manual_signoff"])
        digest = hashlib.sha256(report_path.read_bytes()).hexdigest().upper()
        self.assertEqual(report, verify_audit_report(report_path, project_root=self.root, expected_sha256=digest))
        with self.assertRaisesRegex(AuditError, "refusing to overwrite"):
            write_audit_report(
                report_path,
                project_root=self.root,
                subject=subject,
                evidence_bundle_path=bundle_path,
            )

    def test_report_reads_only_an_explicit_hash_bound_human_signoff(self) -> None:
        bundle_path, _, _ = self._write_complete_bundle()
        subject = self._subject()
        record_signoff(
            self.run_path,
            artifact_id="final-video",
            reviewer="Human Reviewer",
            decision="approved",
            note="Watched at normal speed",
            reviewed_at="2026-09-01T00:00:00Z",
        )
        report_path = self.root / "artifacts" / "derived" / "signed-audit-report.json"
        report = write_audit_report(
            report_path,
            project_root=self.root,
            subject=subject,
            evidence_bundle_path=bundle_path,
            signoff_run_manifest_path=self.run_path,
            created_at_utc="2026-09-01T00:00:01Z",
        )
        self.assertEqual("approved", report["manual_signoff"]["state"])
        self.assertEqual("Human Reviewer", report["manual_signoff"]["record"]["reviewer"])
        self.assertFalse(report["automated_audit"]["manual_approval_granted"])
        verify_audit_report(report_path, project_root=self.root)

    def test_mutated_evidence_invalidates_an_existing_report(self) -> None:
        bundle_path, _, submissions = self._write_complete_bundle()
        subject = self._subject()
        report_path = self.root / "artifacts" / "derived" / "audit-report.json"
        write_audit_report(
            report_path,
            project_root=self.root,
            subject=subject,
            evidence_bundle_path=bundle_path,
        )
        Path(submissions[0]["path"]).write_bytes(b"mutated after audit")
        with self.assertRaisesRegex(AuditError, "does not match"):
            verify_audit_report(report_path, project_root=self.root)


if __name__ == "__main__":
    unittest.main()
