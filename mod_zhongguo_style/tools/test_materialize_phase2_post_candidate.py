#!/usr/bin/env python3
"""Focused tests for Phase2 post-candidate materialization."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


TOOLS_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = TOOLS_DIRECTORY.parents[1]
REPOSITORY_TOOLS = REPOSITORY_ROOT / "tools"
for entry in (TOOLS_DIRECTORY, REPOSITORY_TOOLS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from promo_toolchain_loader import ensure_promo_toolchain  # noqa: E402

ensure_promo_toolchain()

from xar_promo.media import parse_ffprobe_json  # noqa: E402
from xar_promo.operations import preserve_artifact, start_run  # noqa: E402
from xar_promo.process import CommandResult  # noqa: E402

import build_phase2_promo_video as builder  # noqa: E402
import materialize_phase2_post_candidate as post  # noqa: E402
from validate_phase2_authoring_claims import (  # noqa: E402
    materialize_ledger,
    project_cue_input,
)


PROMO_DIRECTORY = REPOSITORY_ROOT / "mod_zhongguo_style" / "promo"


class PostCandidateMaterializerTests(unittest.TestCase):
    def _candidate(self, root: Path, cut_id: str):
        cut = builder.cut_for_id(cut_id)
        source_config = PROMO_DIRECTORY / cut.project_config_name
        source_ledger = PROMO_DIRECTORY / cut.authoring_ledger_name
        config = json.loads(source_config.read_text(encoding="utf-8-sig"))
        errors: list[str] = []
        ledger = materialize_ledger(source_ledger, errors)
        self.assertEqual([], errors)
        ledger_by_id = {row["id"]: row for row in ledger["chapters"]}
        for chapter in config["chapters"]:
            cue = project_cue_input(ledger_by_id[chapter["id"]]["cue"])
            chapter["state"] = "ready"
            chapter["cues"] = [cue]
            chapter["artifact_ids"] = [
                builder._narration_artifact_id(chapter["id"], cue["id"])
            ]
        config_path = root / cut.project_config_name
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        run_path = start_run(
            config_path,
            run_id=cut.default_run_id,
            run_directory=root / "candidate-run",
        )
        for chapter in config["chapters"]:
            artifact_id = chapter["artifact_ids"][0]
            narration = root / "inputs" / f"{artifact_id}.mp3"
            narration.parent.mkdir(parents=True, exist_ok=True)
            narration.write_bytes((artifact_id + "\n").encode("utf-8"))
            preserve_artifact(
                run_path,
                narration,
                artifact_id=artifact_id,
                collection="derived",
                role="narration",
                label=narration.name,
                media_type="audio/mpeg",
            )
        candidate = root / "inputs" / cut.deliverable_relative_path.name
        candidate.write_bytes(b"exact candidate bytes")
        preserve_artifact(
            run_path,
            candidate,
            artifact_id=cut.deliverable_artifact_id,
            collection="derived",
            role="deliverable",
            label=candidate.name,
            media_type="video/mp4",
        )
        media_preflight = root / "inputs" / "media-preflight.json"
        media_preflight.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "zhongguo-361-phase2-media-environment-preflight",
                    "media": {"ffmpeg_version": "ffmpeg fixture 1"},
                }
            ),
            encoding="utf-8",
        )
        preserve_artifact(
            run_path,
            media_preflight,
            artifact_id=builder.MEDIA_PREFLIGHT_ARTIFACT_ID,
            collection="raw",
            role="preflight",
            label=media_preflight.name,
            media_type="application/json",
        )
        return cut, config_path, run_path, candidate

    @staticmethod
    def _probe(_ffprobe, path, *, audit_directory, command_runner):
        del audit_directory, command_runner
        target = Path(path).resolve()
        is_video = target.suffix.casefold() == ".mp4"
        streams = (
            [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "duration": "24",
                    "avg_frame_rate": "30/1",
                },
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "48000",
                    "channels": 2,
                    "duration": "24",
                },
            ]
            if is_video
            else [
                {
                    "index": 0,
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "sample_rate": "24000",
                    "channels": 1,
                    "duration": "2",
                }
            ]
        )
        return parse_ffprobe_json(
            json.dumps(
                {
                    "streams": streams,
                    "format": {
                        "filename": str(target),
                        "size": str(target.stat().st_size),
                        "duration": "24" if is_video else "2",
                        "format_name": "mov,mp4" if is_video else "mp3",
                    },
                }
            )
        )

    @staticmethod
    def _command_runner(spec, *, audit_directory):
        for partial in spec.partial_artifacts:
            target = partial if partial.is_absolute() or spec.cwd is None else spec.cwd / partial
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"PNG fixture bytes")
        return CommandResult(spec, 0, "", "", "succeeded", audit_directory, ())

    def _args(self, root: Path, cut_id: str, config_path: Path, run_path: Path):
        return SimpleNamespace(
            cut=cut_id,
            project_config=config_path,
            run_manifest=run_path,
            output_root=run_path.parent / "post-candidate",
            export_directory=root / "release-export",
            ffmpeg="ffmpeg-fixture",
            ffprobe="ffprobe-fixture",
            validate_only=False,
        )

    def test_validate_only_is_read_only_and_does_not_probe_or_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cut, config_path, run_path, candidate = self._candidate(
                root, "character-led"
            )
            args = self._args(root, cut.cut_id, config_path, run_path)
            run_before = run_path.read_bytes()
            candidate_before = candidate.read_bytes()
            plan = post.validate_plan(args)
            self.assertEqual("validated-no-write", plan["status"])
            self.assertFalse(args.output_root.exists())
            self.assertFalse(args.export_directory.exists())
            self.assertEqual(run_before, run_path.read_bytes())
            self.assertEqual(candidate_before, candidate.read_bytes())
            self.assertFalse(
                plan["execution_attestation"]["ffprobe_started"]
            )

    def test_materializes_concrete_pending_review_and_policy_per_cut(self) -> None:
        for cut_id in ("character-led", "institution-led"):
            with self.subTest(cut_id=cut_id), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                cut, config_path, run_path, candidate = self._candidate(root, cut_id)
                args = self._args(root, cut.cut_id, config_path, run_path)
                run_before = run_path.read_bytes()
                candidate_before = candidate.read_bytes()
                receipt = post.materialize(
                    args,
                    probe_loader=self._probe,
                    command_runner=self._command_runner,
                )
                self.assertEqual("pending-human-review", receipt["status"])
                self.assertFalse(
                    receipt["human_gates"]["automatic_approval_allowed"]
                )
                self.assertFalse(receipt["execution_attestation"]["approval_recorded"])
                self.assertFalse(receipt["execution_attestation"]["exported"])
                self.assertFalse(receipt["execution_attestation"]["published"])
                self.assertEqual(run_before, run_path.read_bytes())
                self.assertEqual(candidate_before, candidate.read_bytes())
                self.assertFalse(args.export_directory.exists())

                paths = receipt["planned_paths"]
                storyboard = json.loads(Path(paths["storyboard"]).read_text(encoding="utf-8"))
                expected_count = 12 if cut_id == "institution-led" else 10
                self.assertEqual(expected_count, len(storyboard["chapters"]))
                if cut_id == "institution-led":
                    ids = [row["id"] for row in storyboard["chapters"]]
                    self.assertEqual(
                        "phase2_receipt_appeal_pip.reprise1",
                        ids[ids.index("phase2_projects_metrics") + 1],
                    )
                    reprise = next(
                        row for row in storyboard["chapters"] if row["id"].endswith("reprise1")
                    )
                    self.assertEqual(
                        2.0,
                        reprise["end_seconds"] - reprise["start_seconds"],
                    )

                review_template = json.loads(
                    Path(paths["review_template"]).read_text(encoding="utf-8")
                )
                self.assertTrue(review_template["template_only"])
                self.assertFalse(review_template["is_signoff"])
                self.assertFalse(review_template["approval_granted"])
                evidence = json.loads(
                    Path(paths["evidence_bundle"]).read_text(encoding="utf-8")
                )
                self.assertEqual(2, evidence["format_version"])
                self.assertTrue(evidence["entries"])
                policy = json.loads(
                    Path(paths["release_export_policy"]).read_text(encoding="utf-8")
                )
                artifact_ids = {
                    row.get("artifact_id")
                    for row in policy["items"]
                    if row["source_kind"] == "artifact"
                }
                self.assertEqual(
                    {
                        cut.deliverable_artifact_id,
                        f"{cut.cut_id}-automated-audit",
                    },
                    artifact_ids,
                )
                serialized_commands = json.dumps(receipt["commands"], ensure_ascii=False)
                self.assertNotIn("<", serialized_commands)
                self.assertIsNone(receipt["commands"]["publish"])
                self.assertFalse(
                    receipt["commands"]["signoff"]["automatic_execution_allowed"]
                )


if __name__ == "__main__":
    unittest.main()
