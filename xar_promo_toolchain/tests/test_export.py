from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from xar_promo.export import (  # noqa: E402
    MANIFEST_NAME,
    ExportError,
    ReleaseBundleItem,
    ReleaseBundlePolicy,
    export_release_bundle,
    verify_release_bundle,
)
from xar_promo.operations import (  # noqa: E402
    initialize_project,
    preserve_artifact,
    record_signoff,
    start_run,
)
from xar_promo.project import load_document  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class ReleaseBundleExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        self.config_path, _ = initialize_project(
            self.project,
            project_id="sample",
            title="Sample promo",
            narration_locale="zh-CN",
            subtitle_locales=["zh-CN", "en"],
            adapter="generic",
            preset="default",
            run_id="authoring",
        )
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        config["chapters"] = [
            {
                "id": "intro",
                "type": "video_clip",
                "state": "ready",
                "title": {"zh-CN": "开场", "en": "Opening"},
                "cues": [
                    {
                        "id": "intro-001",
                        "narration": {"zh-CN": "开场。"},
                        "subtitles": {"zh-CN": "开场。", "en": "Opening."},
                    }
                ],
                "artifact_ids": ["final-video"],
            }
        ]
        self.config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.run_path = start_run(self.config_path, run_id="release")
        self.run_root = self.run_path.parent
        self.records = {}
        self._preserve("final-video", "deliverable", "final.mp4", b"final video")
        self._preserve("subtitle-zh", "subtitle", "zh-CN.ass", b"zh subtitles")
        self._preserve("subtitle-en", "subtitle", "en.ass", b"en subtitles")
        self._preserve("thumbnail", "thumbnail", "thumbnail.png", b"thumbnail")
        self._preserve("release-sidecar", "sidecar", "release.json", b'{"release":true}')
        self._preserve("visual-audit", "audit", "audit.json", b'{"status":"GREEN"}')
        self._preserve("raw-capture", "capture", "raw.mp4", b"raw process material")
        record_signoff(
            self.run_path,
            artifact_id="final-video",
            reviewer="Human Reviewer",
            decision="approved",
            note="Watched at normal speed",
            reviewed_at="2026-09-01T00:00:00Z",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _preserve(self, artifact_id: str, role: str, name: str, payload: bytes):
        source = Path(self.temporary.name) / "inputs" / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(payload)
        record = preserve_artifact(
            self.run_path,
            source,
            artifact_id=artifact_id,
            collection="derived" if role != "capture" else "raw",
            role=role,
            label=name,
            media_type="application/octet-stream",
        )
        self.records[artifact_id] = record
        return record

    def _policy(self, *, deliverable_id: str = "final-video") -> ReleaseBundlePolicy:
        return ReleaseBundlePolicy(
            (
                ReleaseBundleItem.artifact(
                    category="audit",
                    destination="evidence/visual-audit.json",
                    artifact_id="visual-audit",
                    expected_role="audit",
                ),
                ReleaseBundleItem.artifact(
                    category="deliverable",
                    destination="video/promo.mp4",
                    artifact_id=deliverable_id,
                    expected_role="deliverable",
                ),
                ReleaseBundleItem.project_config_snapshot(
                    destination="metadata/project-config.json"
                ),
                ReleaseBundleItem.artifact(
                    category="sidecar",
                    destination="metadata/release-sidecar.json",
                    artifact_id="release-sidecar",
                    expected_role="sidecar",
                ),
                ReleaseBundleItem.artifact(
                    category="thumbnail",
                    destination="thumbnail.png",
                    artifact_id="thumbnail",
                    expected_role="thumbnail",
                ),
                ReleaseBundleItem.artifact(
                    category="subtitle",
                    destination="subtitles/zh-CN.ass",
                    artifact_id="subtitle-zh",
                    expected_role="subtitle",
                ),
            )
        )

    def test_export_is_deterministic_exact_allowlist_and_source_preserving(self) -> None:
        run_before = self.run_path.read_bytes()
        source_before = {
            artifact_id: (self.run_root / record.path).read_bytes()
            for artifact_id, record in self.records.items()
        }
        first = Path(self.temporary.name) / "release-one"
        second = Path(self.temporary.name) / "release-two"
        first_manifest = export_release_bundle(
            self.run_path, first, policy=self._policy()
        )
        second_manifest = export_release_bundle(
            self.run_path, second, policy=self._policy()
        )

        self.assertEqual(first_manifest, second_manifest)
        self.assertEqual(
            (first / MANIFEST_NAME).read_bytes(),
            (second / MANIFEST_NAME).read_bytes(),
        )
        expected = {
            MANIFEST_NAME,
            "evidence/visual-audit.json",
            "metadata/project-config.json",
            "metadata/release-sidecar.json",
            "subtitles/zh-CN.ass",
            "thumbnail.png",
            "video/promo.mp4",
        }
        actual = {
            path.relative_to(first).as_posix()
            for path in first.rglob("*")
            if path.is_file()
        }
        self.assertEqual(expected, actual)
        self.assertFalse((first / "subtitles/en.ass").exists())
        self.assertNotIn("raw-capture", (first / MANIFEST_NAME).read_text(encoding="utf-8"))
        verified = verify_release_bundle(first)
        self.assertEqual(first_manifest, verified)
        self.assertEqual(run_before, self.run_path.read_bytes())
        for artifact_id, payload in source_before.items():
            self.assertEqual(payload, (self.run_root / self.records[artifact_id].path).read_bytes())

    def test_existing_destination_is_never_overwritten(self) -> None:
        destination = Path(self.temporary.name) / "existing"
        destination.mkdir()
        marker = destination / "keep.txt"
        marker.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(ExportError, "refusing to overwrite"):
            export_release_bundle(self.run_path, destination, policy=self._policy())
        self.assertEqual("keep", marker.read_text(encoding="utf-8"))

    def test_selected_deliverable_requires_its_own_explicit_approval(self) -> None:
        self._preserve("unapproved-video", "deliverable", "unapproved.mp4", b"unapproved")
        destination = Path(self.temporary.name) / "unapproved-export"
        with self.assertRaisesRegex(ExportError, "not explicitly approved"):
            export_release_bundle(
                self.run_path,
                destination,
                policy=self._policy(deliverable_id="unapproved-video"),
            )
        self.assertFalse(destination.exists())

    def test_hash_drift_is_rejected_without_creating_output(self) -> None:
        selected = self.records["subtitle-zh"]
        (self.run_root / selected.path).write_bytes(b"changed after preservation")
        destination = Path(self.temporary.name) / "drifted-export"
        with self.assertRaisesRegex(ExportError, "not release-ready"):
            export_release_bundle(self.run_path, destination, policy=self._policy())
        self.assertFalse(destination.exists())

    def test_policy_role_mismatch_is_rejected(self) -> None:
        items = list(self._policy().items)
        items[-1] = ReleaseBundleItem.artifact(
            category="subtitle",
            destination="subtitles/zh-CN.ass",
            artifact_id="subtitle-zh",
            expected_role="sidecar",
        )
        with self.assertRaisesRegex(ExportError, "caller-required role"):
            export_release_bundle(
                self.run_path,
                Path(self.temporary.name) / "bad-role",
                policy=ReleaseBundlePolicy(tuple(items)),
            )

    def test_bundle_reverification_rejects_mutation_and_extra_files(self) -> None:
        mutated = Path(self.temporary.name) / "mutated"
        export_release_bundle(self.run_path, mutated, policy=self._policy())
        (mutated / "video" / "promo.mp4").write_bytes(b"mutated")
        with self.assertRaisesRegex(ExportError, "hash drift"):
            verify_release_bundle(mutated)

        extra = Path(self.temporary.name) / "extra"
        export_release_bundle(self.run_path, extra, policy=self._policy())
        (extra / "unexpected.txt").write_text("not allowlisted", encoding="utf-8")
        with self.assertRaisesRegex(ExportError, "differs from its allowlist"):
            verify_release_bundle(extra)


if __name__ == "__main__":
    unittest.main()
