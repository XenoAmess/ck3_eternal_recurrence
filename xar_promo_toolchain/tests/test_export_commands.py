from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

import xar_promo.export_commands as commands  # noqa: E402
from xar_promo.operations import (  # noqa: E402
    initialize_project,
    preserve_artifact,
    record_signoff,
    start_run,
)


class ExportCommandHandlerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.temporary_root = Path(self.temporary.name)
        project = self.temporary_root / "project"
        config_path, _ = initialize_project(
            project,
            project_id="sample",
            title="Sample",
            narration_locale="zh-CN",
            subtitle_locales=["zh-CN", "en"],
            adapter="generic",
            preset="default",
            run_id="authoring",
        )
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["chapters"] = [
            {
                "id": "intro",
                "type": "video_clip",
                "state": "ready",
                "title": {"zh-CN": "开场"},
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
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.run_path = start_run(config_path, run_id="release")
        self._preserve("final-video", "deliverable", b"final video")
        self._preserve("subtitle-zh", "subtitle", b"subtitles")
        record_signoff(
            self.run_path,
            artifact_id="final-video",
            reviewer="Human Reviewer",
            decision="approved",
            note=None,
            reviewed_at="2026-09-01T00:00:00Z",
        )
        self.policy_path = self.temporary_root / "release-policy.json"
        self._write_policy()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _preserve(self, artifact_id: str, role: str, payload: bytes) -> None:
        source = self.temporary_root / "inputs" / f"{artifact_id}.bin"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(payload)
        preserve_artifact(
            self.run_path,
            source,
            artifact_id=artifact_id,
            collection="derived",
            role=role,
            label=artifact_id,
            media_type="application/octet-stream",
        )

    def _policy(self, deliverable_id: str = "final-video") -> dict:
        return {
            "format_version": 1,
            "kind": commands.POLICY_KIND,
            "items": [
                {
                    "category": "subtitle",
                    "destination": "subtitles/zh-CN.ass",
                    "source_kind": "artifact",
                    "artifact_id": "subtitle-zh",
                    "expected_role": "subtitle",
                },
                {
                    "category": "deliverable",
                    "destination": "video/promo.mp4",
                    "source_kind": "artifact",
                    "artifact_id": deliverable_id,
                    "expected_role": "deliverable",
                },
                {
                    "category": "project-config",
                    "destination": "metadata/project-config.json",
                    "source_kind": "project-config-snapshot",
                },
            ],
        }

    def _write_policy(self, value: dict | None = None) -> None:
        self.policy_path.write_text(
            json.dumps(value or self._policy(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_policy_requires_explicit_artifact_ids_and_returns_sorted_allowlist(self) -> None:
        policy = commands.load_export_policy(self.policy_path)
        self.assertEqual(
            [
                "metadata/project-config.json",
                "subtitles/zh-CN.ass",
                "video/promo.mp4",
            ],
            [item.destination for item in policy.items],
        )
        invalid = self._policy()
        del invalid["items"][1]["artifact_id"]
        self._write_policy(invalid)
        with self.assertRaisesRegex(commands.ExportPolicyError, "explicitly contain"):
            commands.load_export_policy(self.policy_path)

    def test_validate_only_and_dry_run_are_read_only(self) -> None:
        run_before = self.run_path.read_bytes()
        for flag in ("validate_only", "dry_run"):
            with self.subTest(flag=flag):
                parent = self.temporary_root / f"not-created-{flag}"
                destination = parent / "bundle"
                kwargs = {flag: True}
                with mock.patch.object(commands, "export_release_bundle") as exporter:
                    result = commands.handle_export_command(
                        self.run_path,
                        destination,
                        self.policy_path,
                        **kwargs,
                    )
                self.assertEqual(0, result.exit_code)
                self.assertEqual("GREEN", result.status)
                self.assertTrue(result.release_validated)
                self.assertFalse(result.exported)
                self.assertFalse(parent.exists())
                exporter.assert_not_called()
        self.assertEqual(run_before, self.run_path.read_bytes())

    def test_export_mode_returns_structured_success_and_creates_bundle(self) -> None:
        destination = self.temporary_root / "release-bundle"
        result = commands.handle_export_command(
            self.run_path,
            destination,
            self.policy_path,
        )
        self.assertEqual(0, result.exit_code)
        self.assertEqual("export", result.mode)
        self.assertTrue(result.release_validated)
        self.assertTrue(result.exported)
        self.assertIsNotNone(result.manifest)
        self.assertTrue((destination / "release-bundle-manifest.json").is_file())
        structured = result.to_dict()
        self.assertFalse(structured["network_used"])
        self.assertFalse(structured["publish_performed"])
        self.assertEqual(0, structured["exit_code"])

    def test_unapproved_selected_deliverable_returns_two_without_output(self) -> None:
        self._preserve("unapproved-video", "deliverable", b"unapproved")
        self._write_policy(self._policy("unapproved-video"))
        destination = self.temporary_root / "unapproved-output"
        result = commands.handle_export_command(
            self.run_path,
            destination,
            self.policy_path,
        )
        self.assertEqual(2, result.exit_code)
        self.assertEqual("RED", result.status)
        self.assertTrue(result.release_validated)
        self.assertIn("not explicitly approved", result.error)
        self.assertFalse(destination.exists())

    def test_bad_policy_returns_two_and_does_not_create_destination_parent(self) -> None:
        bad = self._policy()
        bad["items"][0]["unexpected_secret"] = "must not be accepted"
        self._write_policy(bad)
        parent = self.temporary_root / "absent-parent"
        result = commands.handle_export_command(
            self.run_path,
            parent / "bundle",
            self.policy_path,
            validate_only=True,
        )
        self.assertEqual(2, result.exit_code)
        self.assertFalse(result.release_validated)
        self.assertFalse(parent.exists())

    def test_overwrite_and_conflicting_read_only_flags_return_two(self) -> None:
        destination = self.temporary_root / "existing"
        destination.mkdir()
        marker = destination / "keep.txt"
        marker.write_text("keep", encoding="utf-8")
        overwrite = commands.handle_export_command(
            self.run_path,
            destination,
            self.policy_path,
        )
        self.assertEqual(2, overwrite.exit_code)
        self.assertTrue(overwrite.release_validated)
        self.assertEqual("keep", marker.read_text(encoding="utf-8"))

        conflict_parent = self.temporary_root / "flag-conflict"
        conflict = commands.handle_export_command(
            self.run_path,
            conflict_parent / "bundle",
            self.policy_path,
            dry_run=True,
            validate_only=True,
        )
        self.assertEqual(2, conflict.exit_code)
        self.assertEqual("invalid", conflict.mode)
        self.assertFalse(conflict_parent.exists())


if __name__ == "__main__":
    unittest.main()
