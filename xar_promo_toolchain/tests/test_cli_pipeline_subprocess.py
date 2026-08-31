from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PACKAGE_ROOT / "src"
TESTS_ROOT = Path(__file__).resolve().parent
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from xar_promo.evidence import (  # noqa: E402
    bind_external_artifact,
    write_evidence_bundle,
    write_sampling_plan,
)
from xar_promo.model import new_project_config  # noqa: E402
from xar_promo.operations import start_run  # noqa: E402
from xar_promo.project import load_document  # noqa: E402
from xar_promo.runlog import (  # noqa: E402
    append_automated_audit_record,
    append_phase_record,
    automated_audit_records_from_run,
    phase_records_from_run,
)


class PipelineCliSubprocessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.sandbox = Path(self.temporary.name)
        self.project = self.sandbox / "project"
        self.project.mkdir()
        config = new_project_config(
            "cli-pipeline-test",
            "CLI Pipeline Test",
            "und",
            ["und"],
            "fake-adapter",
            "fake-preset",
        ).to_dict()
        config["constraints"]["duration_limit_seconds"] = 30
        config["chapters"] = [
            {
                "id": "chapter-001",
                "type": "feature",
                "state": "ready",
                "title": {"und": "Feature"},
                "cues": [
                    {
                        "id": "cue-001",
                        "narration": {"und": "Narration"},
                        "subtitles": {"und": "Subtitle"},
                    }
                ],
                "artifact_ids": [],
            }
        ]
        self.config_path = self.project / "promo-project.json"
        self.config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.run_path = start_run(self.config_path, run_id="cli-run")
        self.visual = self.sandbox / "inputs" / "visual.png"
        self.narration = self.sandbox / "inputs" / "narration.wav"
        self.visual.parent.mkdir()
        self.visual.write_bytes(b"CLI prepared visual")
        self.narration.write_bytes(b"CLI prepared narration")

        plugin_root = self.sandbox / "entry-points"
        distribution = plugin_root / "xar_promo_cli_fixtures-1.0.dist-info"
        distribution.mkdir(parents=True)
        (distribution / "METADATA").write_text(
            "Metadata-Version: 2.1\n"
            "Name: xar-promo-cli-fixtures\n"
            "Version: 1.0\n",
            encoding="utf-8",
        )
        (distribution / "entry_points.txt").write_text(
            "[xar_promo.adapters]\n"
            "fake-adapter = _pipeline_cli_fixture:adapter_factory\n"
            "\n"
            "[xar_promo.presets]\n"
            "fake-preset = _pipeline_cli_fixture:preset_factory\n",
            encoding="utf-8",
        )
        self.environment = os.environ.copy()
        python_paths = [str(SOURCE_ROOT), str(TESTS_ROOT), str(plugin_root)]
        existing = self.environment.get("PYTHONPATH")
        if existing:
            python_paths.append(existing)
        self.environment["PYTHONPATH"] = os.pathsep.join(python_paths)
        self.environment["PYTHONDONTWRITEBYTECODE"] = "1"
        self.environment["PYTHONUTF8"] = "1"
        self.environment["XAR_PROMO_CLI_FIXTURE_VISUAL"] = str(self.visual)
        self.environment["XAR_PROMO_CLI_FIXTURE_NARRATION"] = str(self.narration)
        self.environment["XAR_PROMO_CLI_FIXTURE_MODE"] = "success"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def invoke(
        self,
        *arguments: object,
        expected: int,
        mode: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = self.environment.copy()
        if mode is not None:
            environment["XAR_PROMO_CLI_FIXTURE_MODE"] = mode
        completed = subprocess.run(
            [sys.executable, "-m", "xar_promo", *(str(value) for value in arguments)],
            cwd=self.sandbox,
            env=environment,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            expected,
            completed.returncode,
            msg=(
                f"args={arguments!r}\nstdout={completed.stdout}\n"
                f"stderr={completed.stderr}"
            ),
        )
        self.assertNotIn("Traceback", completed.stdout)
        self.assertNotIn("Traceback", completed.stderr)
        return completed

    def history_files(self) -> set[Path]:
        return set(
            (self.run_path.parent / "artifacts" / "manifest-history").rglob(
                "*.json"
            )
        )

    @staticmethod
    def json_stream(value: str) -> dict[str, object]:
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise AssertionError("CLI JSON result must be an object")
        return parsed

    def test_plan_run_manifest_is_byte_history_and_workdir_read_only(self) -> None:
        before_manifest = self.run_path.read_bytes()
        before_history = self.history_files()
        workdir = self.sandbox / "plan-must-not-exist"
        completed = self.invoke(
            "plan",
            self.run_path,
            "--workdir",
            workdir,
            "--composer",
            "_pipeline_cli_fixture:compose",
            "--validate-only",
            expected=0,
        )
        self.assertEqual("", completed.stderr)
        payload = self.json_stream(completed.stdout)
        self.assertEqual(0, payload["exit_status"])
        self.assertEqual("validated", payload["pipeline"]["status"])
        self.assertEqual(before_manifest, self.run_path.read_bytes())
        self.assertEqual(before_history, self.history_files())
        self.assertFalse(workdir.exists())

    def test_build_typed_phase_history_remains_appendable(self) -> None:
        completed = self.invoke(
            "build",
            self.run_path,
            "--workdir",
            self.sandbox / "successful-build",
            "--composer",
            "_pipeline_cli_fixture:compose",
            expected=0,
        )
        self.assertEqual("", completed.stderr)
        payload = self.json_stream(completed.stdout)
        self.assertEqual("succeeded", payload["pipeline"]["status"])
        run = load_document(self.run_path).run
        phases = phase_records_from_run(run)
        self.assertGreater(len(phases), 1)
        appended = append_phase_record(
            self.run_path,
            phase_id="subprocess.follow-up",
            status="succeeded",
            recorded_at="2026-09-01T00:10:00Z",
        )
        self.assertEqual(len(phases) + 1, appended.sequence)
        self.assertEqual(
            len(phases) + 1,
            len(phase_records_from_run(load_document(self.run_path).run)),
        )

    def test_build_red_is_exit_two_retained_typed_and_traceback_free(self) -> None:
        completed = self.invoke(
            "build",
            self.run_path,
            "--workdir",
            self.sandbox / "failed-build",
            "--composer",
            "_pipeline_cli_fixture:compose",
            expected=2,
            mode="build-failure",
        )
        self.assertEqual("", completed.stdout)
        payload = self.json_stream(completed.stderr)
        self.assertEqual(2, payload["exit_status"])
        self.assertEqual("failed", payload["pipeline"]["status"])
        self.assertEqual("cli retained stdout", payload["pipeline"]["failure"]["stdout"])
        run = load_document(self.run_path).run
        phases = phase_records_from_run(run)
        self.assertIn("build.failure-materials", {record.phase_id for record in phases})
        roles = {record.role for record in run.artifacts}
        self.assertTrue(
            {"partial-output", "process-stdout", "process-stderr"}.issubset(roles)
        )

    def _build_subject_and_evidence(self) -> Path:
        completed = self.invoke(
            "build",
            self.run_path,
            "--workdir",
            self.sandbox / "audit-subject-build",
            "--composer",
            "_pipeline_cli_fixture:compose",
            expected=0,
        )
        self.assertEqual("", completed.stderr)
        run = load_document(self.run_path).run
        subject = next(
            record for record in run.artifacts if record.artifact_id == "final-video"
        )
        subject_path = self.run_path.parent / Path(subject.path)
        producer_source = {
            "adapter_id": "cli-source",
            "tool": "cli-recorder",
            "tool_version": "1",
            "operation": "capture",
            "execution": "external",
        }
        producer_frame = {
            "adapter_id": "cli-frame",
            "tool": "cli-frame",
            "tool_version": "1",
            "operation": "extract-frame",
            "execution": "external",
        }
        producer_ocr = {
            "adapter_id": "cli-ocr",
            "tool": "cli-ocr",
            "tool_version": "1",
            "operation": "ocr-frame",
            "execution": "external",
        }
        source = bind_external_artifact(
            subject_path,
            project_root=self.run_path.parent,
            artifact_id="cli-audit-source",
            collection="derived",
            role="capture",
            label="CLI audit source",
            media_type="video/mp4",
            producer=producer_source,
        )
        inputs = self.run_path.parent / "cli-audit-inputs"
        plan_path = inputs / "plan.json"
        plan = write_sampling_plan(
            plan_path,
            [
                {
                    "id": "chapter-001",
                    "kind": "video",
                    "source": source,
                    "start_seconds": 0,
                    "end_seconds": 0,
                }
            ],
            project_root=self.run_path.parent,
            interval_seconds=1,
            frame_producer=producer_frame,
            ocr_producer=producer_ocr,
        )
        submissions = []
        for sample in plan["samples"]:
            for role, producer, media_type in (
                ("frame", producer_frame, "image/png"),
                ("ocr", producer_ocr, "application/json"),
            ):
                path = inputs / f"{sample['id']}-{role}.bin"
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
        bundle_path = inputs / "bundle.json"
        write_evidence_bundle(
            bundle_path,
            project_root=self.run_path.parent,
            plan_path=plan_path,
            submissions=submissions,
        )
        return bundle_path

    def test_audit_typed_record_remains_appendable_and_never_signs_off(self) -> None:
        bundle_path = self._build_subject_and_evidence()
        completed = self.invoke(
            "audit",
            self.run_path,
            "--subject-artifact-id",
            "final-video",
            "--evidence-bundle",
            bundle_path,
            "--report",
            "cli-audit-output/report.json",
            "--report-artifact-id",
            "cli-audit-report",
            "--created-at-utc",
            "2026-09-01T00:20:00Z",
            expected=0,
        )
        self.assertEqual("", completed.stderr)
        payload = self.json_stream(completed.stdout)
        self.assertEqual({"state": "not-provided"}, payload["audit"]["manual_signoff"])
        run = load_document(self.run_path).run
        audits = automated_audit_records_from_run(run)
        self.assertEqual(1, len(audits))
        self.assertEqual((), run.signoffs)
        appended = append_automated_audit_record(
            self.run_path,
            check_id="subprocess-follow-up",
            status="passed",
            subject_artifact_id="final-video",
            report_artifact_id="cli-audit-report",
            recorded_at="2026-09-01T00:21:00Z",
        )
        self.assertEqual(2, appended.sequence)
        self.assertEqual(
            2,
            len(automated_audit_records_from_run(load_document(self.run_path).run)),
        )
        self.assertEqual((), load_document(self.run_path).run.signoffs)

    def test_plan_build_and_audit_operational_reds_are_exit_two_without_traceback(self) -> None:
        before = self.run_path.read_bytes()
        bad_plan = self.invoke(
            "plan",
            self.run_path,
            "--workdir",
            self.sandbox / "bad-plan-work",
            "--composer",
            "missing-colon",
            expected=2,
        )
        self.assertEqual("", bad_plan.stdout)
        self.assertTrue(bad_plan.stderr.startswith("RED: composer must use"))
        self.assertEqual(before, self.run_path.read_bytes())

        bad_audit = self.invoke(
            "audit",
            self.run_path,
            "--subject-artifact-id",
            "missing-subject",
            "--evidence-bundle",
            self.sandbox / "missing-bundle.json",
            "--report",
            self.sandbox / "must-not-exist.json",
            "--report-artifact-id",
            "missing-audit-report",
            expected=2,
        )
        self.assertEqual("", bad_audit.stdout)
        audit_payload = self.json_stream(bad_audit.stderr)
        self.assertEqual(2, audit_payload["exit_status"])
        self.assertEqual("ArtifactError", audit_payload["failure"]["exception_type"])


if __name__ == "__main__":
    unittest.main()
