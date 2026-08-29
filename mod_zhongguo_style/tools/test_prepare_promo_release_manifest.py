#!/usr/bin/env python3
"""Offline tests for the GREEN-capture promo manifest projection."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


TOOLS_DIRECTORY = Path(__file__).resolve().parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import build_promo_video as promo  # noqa: E402
import prepare_promo_release_manifest as prepare  # noqa: E402
import validate_promo_video as validator  # noqa: E402


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _make_capture(root: Path, *, result: str = "GREEN") -> Path:
    raw = root / "cell" / "promo" / "raw" / "zg361-promo-live-full-take-01.mkv"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"synthetic media bytes for manifest-only offline test")
    for mechanism_id in prepare.POLICY_IDS:
        path = root / "cell" / f"12_policy_{mechanism_id:03d}_event.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"synthetic policy {mechanism_id:03d}".encode("ascii"))
    (root / "cell" / "10_superior_result.png").write_bytes(
        b"synthetic superior receipt"
    )

    marks = [
        {"label": label, "seconds": float(index * 10 + 1)}
        for index, label in enumerate(prepare.REQUIRED_MARKS)
    ]
    timeline = {
        "schema": 1,
        "exclude_ck3_loading": True,
        "source_kind": "real CK3 1.19.0.6 desktop capture after gameplay HUD",
        "raw_path": str(raw.resolve()),
        "raw_bytes": raw.stat().st_size,
        "raw_sha256": _sha(raw),
        "marks": marks,
    }
    timeline_path = root / "cell" / "promo" / "capture-timeline.json"
    _write_json(timeline_path, timeline)
    report = {
        "schema_version": 1,
        "result": result,
        "cell": {
            "result": result,
            "promo_capture": copy.deepcopy(timeline),
            "scenario_evidence": {
                "promo_received_scoreboard": {
                    "received_panel_artifact": "11_received_scoreboard.png"
                },
                "promo_policy_cards": [
                    {
                        "mechanism_id": mechanism_id,
                        "event_artifact": f"12_policy_{mechanism_id:03d}_event.png",
                    }
                    for mechanism_id in prepare.POLICY_IDS
                ],
            },
        },
    }
    report_path = root / "report.json"
    _write_json(report_path, report)

    indexed_paths = [
        report_path,
        timeline_path,
        raw,
        root / "cell" / "10_superior_result.png",
        *[
            root / "cell" / f"12_policy_{mechanism_id:03d}_event.png"
            for mechanism_id in prepare.POLICY_IDS
        ],
    ]
    index = {
        "schema_version": 1,
        "result": result,
        "artifact_root": str(root.resolve()),
        "files": [
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _sha(path),
            }
            for path in indexed_paths
        ],
    }
    _write_json(root / "evidence-index.json", index)
    return root


class PromoReleaseProjectionTests(unittest.TestCase):
    def test_green_capture_projects_zero_placeholder_release_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capture = _make_capture(root / "green-capture")
            payload, provenance = prepare.project_manifest(artifact_root=capture)
            output = root / "captured-release-manifest.json"
            _write_json(output, payload)

            loaded, chapters = promo.load_manifest(output)
            self.assertEqual("captured_release_candidate", loaded["project_status"])
            self.assertEqual(0, loaded["_placeholder_count"])
            self.assertEqual(18, len(chapters))
            self.assertEqual(
                {"01-who-rates-whom", "09-pip-bottom", "15-honest-boundary"},
                {
                    chapter.chapter_id
                    for chapter in chapters
                    if chapter.classification == "generated-evidence-boundary"
                },
            )
            self.assertEqual(
                list(prepare.POLICY_IDS), provenance["policy_card_ids"]
            )

            policy_sources = {
                int(Path(chapter.raw["source"]["path"]).stem.split("_")[2])
                for chapter in chapters
                if "policy card #" in chapter.raw.get("source", {}).get("label", "")
            }
            self.assertEqual(set(prepare.POLICY_IDS), policy_sources)
            for chapter in chapters:
                records = []
                if "source" in chapter.raw:
                    records.append(chapter.raw["source"])
                records.extend(chapter.raw.get("evidence_sources", []))
                for record in records:
                    self.assertTrue(Path(record["path"]).is_absolute())
                    self.assertEqual(64, len(record["sha256"]))
                    self.assertEqual(Path(record["path"]).stat().st_size, record["bytes"])

            with (
                mock.patch.object(promo.shared, "preflight_video_sources"),
                mock.patch.object(promo, "prepare_subtitle_layouts"),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                release, release_chapters = validator.validate_project(
                    output, stage="release"
                )
            self.assertEqual(0, release["_placeholder_count"])
            self.assertEqual(18, len(release_chapters))

    def test_authoring_narration_and_jokes_survive_projection(self) -> None:
        base = json.loads(
            prepare.DEFAULT_BASE_MANIFEST.read_text(encoding="utf-8-sig")
        )
        with tempfile.TemporaryDirectory() as temporary:
            capture = _make_capture(Path(temporary) / "green-capture")
            payload, _provenance = prepare.project_manifest(artifact_root=capture)
        projected_pairs = {
            (cue["zh"], cue["en"])
            for chapter in payload["chapters"]
            for cue in chapter["cues"]
        }
        boundary_original = base["chapters"][15]["cues"][0]
        for chapter in base["chapters"]:
            for cue in chapter["cues"]:
                if cue is boundary_original:
                    continue
                self.assertIn((cue["zh"], cue["en"]), projected_pairs)
        corpus = " ".join(cue["zh"] for chapter in payload["chapters"] for cue in chapter["cues"])
        for joke in ("今年这个 C", "别问涨薪", "算盘终于没有闹鬼", "下一场校准会"):
            self.assertIn(joke, corpus)

    def test_red_capture_and_missing_marks_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            red = _make_capture(root / "red-capture", result="RED")
            with self.assertRaisesRegex(prepare.PrepareError, "must be GREEN"):
                prepare.project_manifest(artifact_root=red)

            green = _make_capture(root / "missing-mark")
            timeline_path = green / "cell" / "promo" / "capture-timeline.json"
            timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
            timeline["marks"] = [
                row
                for row in timeline["marks"]
                if row["label"] != "policy_card_361_visible"
            ]
            _write_json(timeline_path, timeline)
            # Update only the index hash; the report still carries the original
            # timeline, proving that either missing marks or provenance drift is RED.
            index_path = green / "evidence-index.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            for row in index["files"]:
                if row["path"] == "cell/promo/capture-timeline.json":
                    row["bytes"] = timeline_path.stat().st_size
                    row["sha256"] = _sha(timeline_path)
            _write_json(index_path, index)
            with self.assertRaisesRegex(prepare.PrepareError, "missing marks"):
                prepare.project_manifest(artifact_root=green)

    def test_write_is_append_only_and_records_manifest_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capture = _make_capture(root / "green-capture")
            output = root / "deliverable" / "captured-release-manifest.json"
            manifest_path, provenance_path = prepare.write_projection(
                artifact_root=capture, output=output
            )
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            self.assertEqual(_sha(manifest_path).upper(), provenance["output_manifest"]["sha256"])
            original = manifest_path.read_bytes()
            with self.assertRaisesRegex(prepare.PrepareError, "refusing to overwrite"):
                prepare.write_projection(artifact_root=capture, output=output)
            self.assertEqual(original, manifest_path.read_bytes())

    def test_loader_rejects_a_declared_source_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capture = _make_capture(root / "green-capture")
            payload, _provenance = prepare.project_manifest(artifact_root=capture)
            chapter = next(
                row for row in payload["chapters"] if row["id"] == "02-okr-kpi"
            )
            chapter["source"]["sha256"] = "0" * 64
            output = root / "tampered.json"
            _write_json(output, payload)
            with self.assertRaisesRegex(promo.PromoError, "sha256 does not match"):
                promo.load_manifest(output)


if __name__ == "__main__":
    unittest.main()
