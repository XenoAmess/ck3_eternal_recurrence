from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import xar_promo
from xar_promo.errors import ManifestError
from xar_promo.operations import (
    initialize_project,
    preserve_artifact,
    record_signoff,
    start_run,
)
from xar_promo.project import load_document, validate_profile


class ConfigRunSplitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "sample"
        self.config_path, self.run_path = initialize_project(
            self.root,
            project_id="sample",
            title="Sample Project",
            narration_locale="und",
            subtitle_locales=["und"],
            adapter="generic",
            preset="default",
            run_id="run-0001",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_public_run_mutations_are_typed(self) -> None:
        self.assertFalse(hasattr(xar_promo, "append_run_records"))
        self.assertTrue(callable(xar_promo.append_phase_record))
        self.assertTrue(callable(xar_promo.append_automated_audit_record))

    def test_init_separates_checked_in_intent_from_run_evidence(self) -> None:
        config = load_document(self.config_path)
        run = load_document(self.run_path)
        self.assertEqual("project-config-v1", config.source_format)
        self.assertEqual("run-manifest-v1", run.source_format)
        self.assertEqual("generic", config.config.adapter)
        self.assertEqual("sample", run.bound_config.project_id)
        self.assertNotIn("artifacts", config.raw)
        self.assertEqual([], run.raw["artifacts"])
        self.assertEqual([], run.raw["phase_history"])
        self.assertEqual([], run.raw["audits"])
        self.assertEqual([], run.raw["signoffs"])

    def test_run_preserves_config_snapshot_across_later_config_edits(self) -> None:
        payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        payload["project"]["title"] = "Changed after run creation"
        self.config_path.write_text(json.dumps(payload), encoding="utf-8")
        original = load_document(self.run_path)
        self.assertEqual("Sample Project", original.bound_config.title)
        second = start_run(self.config_path, run_id="run-after-edit")
        self.assertEqual(
            "Changed after run creation", load_document(second).bound_config.title
        )

    def test_start_run_binds_current_config_and_refuses_overwrite(self) -> None:
        second = start_run(self.config_path, run_id="run-0002")
        loaded = load_document(second)
        self.assertEqual("run-0002", loaded.run.run_id)
        self.assertEqual("sample", loaded.bound_config.project_id)
        with self.assertRaisesRegex(ManifestError, "refusing to overwrite"):
            start_run(self.config_path, run_id="run-0002")

    def test_preserve_is_content_addressed_idempotent_and_keeps_source(self) -> None:
        source = Path(self.temporary.name) / "capture.bin"
        source.write_bytes(b"raw capture bytes")
        first = preserve_artifact(
            self.run_path,
            source,
            artifact_id="capture-01",
            collection="raw",
            role="capture",
            label=None,
            media_type=None,
        )
        second = preserve_artifact(
            self.run_path,
            source,
            artifact_id="capture-01",
            collection="raw",
            role="capture",
            label=None,
            media_type=None,
        )
        self.assertEqual(first, second)
        self.assertTrue(source.is_file())
        self.assertIn(first.sha256, first.path)
        self.assertEqual(1, len(load_document(self.run_path).run.artifacts))

    def test_preserve_and_signoff_archive_each_prior_run_manifest(self) -> None:
        source = Path(self.temporary.name) / "final.mp4"
        source.write_bytes(b"fake final video")
        preserve_artifact(
            self.run_path,
            source,
            artifact_id="final-video",
            collection="derived",
            role="deliverable",
            label="Final video",
            media_type="video/mp4",
        )
        signoff = record_signoff(
            self.run_path,
            artifact_id="final-video",
            reviewer="Human Reviewer",
            decision="approved",
            note="Watched at normal speed",
            reviewed_at="2026-09-01T00:00:00Z",
        )
        self.assertEqual("approved", signoff.decision)
        run = load_document(self.run_path).run
        self.assertEqual(run.artifacts[0].sha256, run.signoffs[0].artifact_sha256)
        history = list((self.run_path.parent / "artifacts" / "manifest-history").rglob("*.json"))
        self.assertEqual(2, len(history))

    def test_signoff_cannot_target_unpreserved_bytes(self) -> None:
        with self.assertRaisesRegex(Exception, "artifact id was not found"):
            record_signoff(
                self.run_path,
                artifact_id="missing",
                reviewer="Reviewer",
                decision="approved",
                note=None,
                reviewed_at="2026-09-01T00:00:00Z",
            )

    def test_authored_config_can_start_a_new_release_ready_run(self) -> None:
        payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        payload["chapters"] = [
            {
                "id": "intro",
                "type": "title_card",
                "state": "ready",
                "title": {"und": "Introduction"},
                "cues": [
                    {
                        "id": "intro-001",
                        "narration": {"und": "Narration"},
                        "subtitles": {"und": "Narration"},
                    }
                ],
                "artifact_ids": ["final-video"],
            }
        ]
        self.config_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        release_run = start_run(self.config_path, run_id="release-candidate")
        source = Path(self.temporary.name) / "release.mp4"
        source.write_bytes(b"release candidate bytes")
        preserve_artifact(
            release_run,
            source,
            artifact_id="final-video",
            collection="derived",
            role="deliverable",
            label="Release candidate",
            media_type="video/mp4",
        )
        record_signoff(
            release_run,
            artifact_id="final-video",
            reviewer="Human Reviewer",
            decision="approved",
            note=None,
            reviewed_at="2026-09-01T00:00:00Z",
        )
        validate_profile(load_document(release_run), "release")


class LegacyCompatibilityTests(unittest.TestCase):
    def test_repository_smoke_manifest_remains_readable(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        legacy = repository / "mod_zhongguo_style" / "promo" / "smoke-manifest.json"
        if not legacy.is_file():
            self.skipTest("monorepo legacy fixture is not present in standalone checkout")
        loaded = load_document(legacy)
        self.assertEqual("legacy-showcase-v1", loaded.source_format)
        self.assertEqual(1, loaded.chapter_count)

    def test_unknown_native_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.json"
            path.write_text('{"format_version": 99, "kind": "unknown"}', encoding="utf-8")
            with self.assertRaises(ManifestError):
                load_document(path)


class BundledSchemaTests(unittest.TestCase):
    def test_project_and_run_v1_schemas_are_bundled_and_distinct(self) -> None:
        root = Path(__file__).resolve().parents[1] / "src" / "xar_promo" / "schemas"
        project = json.loads(
            (root / "promo-project-config-v1.schema.json").read_text(encoding="utf-8")
        )
        run = json.loads(
            (root / "promo-run-manifest-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            "xar_promo_project_config", project["properties"]["kind"]["const"]
        )
        self.assertEqual(
            "xar_promo_run_manifest", run["properties"]["kind"]["const"]
        )
        self.assertIn("project_config", run["required"])
        self.assertIn("signoffs", run["required"])
