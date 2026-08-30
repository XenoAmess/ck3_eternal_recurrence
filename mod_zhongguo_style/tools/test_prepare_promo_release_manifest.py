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


def _record(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": _sha(path),
    }


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _refresh_index_records(root: Path, *paths: Path) -> None:
    index_path = root / "evidence-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    wanted = {path.resolve(): path for path in paths}
    for row in index["files"]:
        absolute = (root / row["path"]).resolve()
        path = wanted.pop(absolute, None)
        if path is not None:
            row["bytes"] = path.stat().st_size
            row["sha256"] = _sha(path)
    if wanted:
        raise AssertionError(f"fixture index did not contain {sorted(map(str, wanted))}")
    _write_json(index_path, index)


def _make_capture(
    root: Path,
    *,
    result: str = "GREEN",
    reviewed_history_id: str = "han_5253",
) -> Path:
    reviewed = prepare.real_characters.reviewed_official(reviewed_history_id)
    history = root / "pinned-game" / "history" / "characters" / "han.txt"
    history.parent.mkdir(parents=True)
    history.write_text(
        f"{reviewed_history_id} = {{\n\tname = ReviewedOfficial\n}}\n"
        "han_8052 = {\n\tname = Shu\n}\n",
        encoding="utf-8",
    )
    title_history = root / "pinned-game" / "history" / "titles" / "e_china.txt"
    title_history.parent.mkdir(parents=True)
    intermediate_liege = ""
    if reviewed["liege_title_id"] != "h_china":
        intermediate_liege = (
            f"{reviewed['liege_title_id']} = {{\n"
            f"\t{reviewed['liege_holder_date']} = {{ holder = "
            f"{reviewed['liege_holder_id']} }}\n"
            "}\n"
        )
    title_history.write_text(
        "h_china = {\n"
        "\t1063.4.30 = { holder = han_8052 }\n"
        "}\n"
        + intermediate_liege
        + f"{reviewed['title_id']} = {{\n"
        f"\t{reviewed['holder_date']} = {{ holder = {reviewed_history_id} "
        f"liege = {reviewed['liege_title_id']} }}\n"
        "}\n",
        encoding="utf-8",
    )
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
    gate_files: list[Path] = []
    clean_frame_gates: list[dict[str, object]] = []
    for span_id in prepare.CLEAN_SPAN_IDS:
        frames: list[dict[str, object]] = []
        for phase in ("begin", "end"):
            samples: list[dict[str, object]] = []
            for sample_index in (1, 2):
                prefix = root / "cell" / "promo" / "clean-gates" / (
                    f"{span_id}-{phase}-sample-{sample_index}"
                )
                image = prefix.with_suffix(".png")
                ocr = prefix.with_name(prefix.name + "-ocr.json")
                image.parent.mkdir(parents=True, exist_ok=True)
                image.write_bytes(
                    f"synthetic clean frame {span_id} {phase} {sample_index}".encode(
                        "utf-8"
                    )
                )
                _write_json(ocr, [{"text": "clean product UI"}])
                gate_files.extend((image, ocr))
                samples.append(
                    {
                        "sample_index": sample_index,
                        "normalized_decisions_header_ocr": "",
                        "image": _record(image),
                        "ocr": _record(ocr),
                    }
                )
            gate_path = root / "cell" / "promo" / "clean-gates" / (
                f"{span_id}-{phase}-gate.json"
            )
            frame = {
                "schema_version": 1,
                "result": "GREEN",
                "span": span_id,
                "phase": phase,
                "full_screen": True,
                "fixture_test_ui_absent": True,
                "native_decisions_drawer_absent": True,
                "forbidden_hits": [],
                "drawer_absence_consecutive_samples": 2,
                "drawer_absence_samples": samples,
                "image": samples[0]["image"],
                "ocr": samples[0]["ocr"],
            }
            _write_json(gate_path, frame)
            gate_files.append(gate_path)
            frame["gate"] = _record(gate_path)
            frames.append(frame)
        clean_frame_gates.append(
            {
                "span_id": span_id,
                "begin_mark": f"{span_id}_clean_begin",
                "end_mark": f"{span_id}_clean_end",
                "result": "GREEN",
                "full_screen": True,
                "fixture_test_ui_absent": True,
                "native_decisions_drawer_absent": True,
                "frames": frames,
            }
        )
    timeline = {
        "schema": 2,
        "exclude_ck3_loading": True,
        "source_kind": "real CK3 1.19.0.6 desktop capture after gameplay HUD",
        "raw_path": str(raw.resolve()),
        "raw_bytes": raw.stat().st_size,
        "raw_sha256": _sha(raw),
        "marks": marks,
        "clean_frame_gates": clean_frame_gates,
        "real_character_provenance": {
            "schema_version": 1,
            "bookmark": {"id": "1066_song", "start_date": "1066.9.15"},
            "subjects": [
                {
                    "history_id": "han_8052",
                    "display_name": "赵曙",
                    "roles": ["manager", "emperor"],
                    "origin": "ck3_history_database",
                    "temporary_or_generated": False,
                    "history_source": _record(history),
                },
                {
                    "history_id": reviewed_history_id,
                    "display_name": reviewed["display_name"],
                    "roles": reviewed["roles"],
                    "origin": "ck3_history_database",
                    "temporary_or_generated": False,
                    "history_source": _record(history),
                },
            ],
            "title_history_source": _record(title_history),
            "title_history_assertions": {
                "h_china_holder_at_start": "han_8052",
                "reviewed_official_title_at_start": reviewed["title_id"],
                "reviewed_official_holder_at_start": reviewed_history_id,
                "reviewed_official_holder_date": reviewed["holder_date"],
                "reviewed_official_title_liege_at_start": reviewed[
                    "liege_title_id"
                ],
                "reviewed_official_direct_liege_holder_at_start": reviewed[
                    "liege_holder_id"
                ],
                "reviewed_official_direct_liege_holder_date": reviewed[
                    "liege_holder_date"
                ],
            },
        },
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
                "reviewed_official_history_id": reviewed_history_id,
                "superior_assigned_player_result": {
                    "reviewed_official_history_id": reviewed_history_id,
                },
                "real_character_runtime_attestation": {
                    "reviewed_official_history_id": reviewed_history_id,
                },
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
        *gate_files,
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
            self.assertEqual(20, len(chapters))
            self.assertEqual(
                {
                    "01-who-rates-whom",
                    "09-pip-bottom",
                    "14-core-loop",
                    "15-honest-boundary",
                },
                {
                    chapter.chapter_id
                    for chapter in chapters
                    if chapter.classification == "generated-evidence-boundary"
                },
            )
            self.assertEqual(
                list(prepare.POLICY_IDS), provenance["policy_card_ids"]
            )
            self.assertEqual(
                list(prepare.CLEAN_SPAN_IDS), provenance["clean_span_ids"]
            )
            self.assertEqual(
                ["han_8052", "han_5253"],
                [
                    row["history_id"]
                    for row in provenance["real_character_provenance"]["subjects"]
                ],
            )

            timeline = json.loads(
                (capture / "cell" / "promo" / "capture-timeline.json").read_text(
                    encoding="utf-8"
                )
            )
            mark_seconds = {
                row["label"]: row["seconds"] for row in timeline["marks"]
            }
            expected_raw = (
                capture
                / "cell"
                / "promo"
                / "raw"
                / "zg361-promo-live-full-take-01.mkv"
            ).resolve()
            used_clean_spans: set[str] = set()
            for chapter in chapters:
                records = []
                if "source" in chapter.raw:
                    records.append(chapter.raw["source"])
                records.extend(chapter.raw.get("evidence_sources", []))
                for record in records:
                    self.assertTrue(Path(record["path"]).is_absolute())
                    self.assertEqual(64, len(record["sha256"]))
                    self.assertEqual(Path(record["path"]).stat().st_size, record["bytes"])
                if chapter.promo_type == "video_clip":
                    self.assertEqual(
                        expected_raw,
                        Path(chapter.raw["source"]["path"]),
                    )
                    capture_record = chapter.raw["capture"]
                    span_id = capture_record["clean_span_id"]
                    used_clean_spans.add(span_id)
                    self.assertEqual(
                        f"{span_id}_clean_begin",
                        capture_record["timeline_start_mark"],
                    )
                    self.assertEqual(
                        f"{span_id}_clean_end",
                        capture_record["timeline_end_mark"],
                    )
                    self.assertEqual(
                        mark_seconds[f"{span_id}_clean_begin"],
                        chapter.raw["start_seconds"],
                    )
                    self.assertEqual(
                        mark_seconds[f"{span_id}_clean_end"],
                        chapter.raw["end_seconds"],
                    )
                    self.assertTrue(
                        capture_record["clean_frame_gate"][
                            "native_decisions_drawer_absent"
                        ]
                    )
                    self.assertNotIn("_visible", capture_record["timeline_start_mark"])
                    self.assertNotIn("_visible", capture_record["timeline_end_mark"])
            self.assertEqual(set(prepare.CLEAN_SPAN_IDS), used_clean_spans)
            self.assertFalse(
                any(chapter.promo_type == "still" for chapter in chapters),
                "policy and product visuals must come from clean raw spans",
            )
            core_loop = next(
                chapter for chapter in chapters if chapter.chapter_id == "14-core-loop"
            )
            self.assertEqual("title_card", core_loop.promo_type)
            self.assertNotIn("source", core_loop.raw)
            self.assertNotIn("start_seconds", core_loop.raw)

            audit_report = root / "visual-audit-report.json"
            _write_json(audit_report, {"result": "GREEN"})
            audit_sha = _sha(audit_report)
            verified_audit = {
                "evaluation": {
                    "result": "GREEN",
                    "release_manifest": {
                        "path": str(output.resolve()),
                        "bytes": output.stat().st_size,
                        "sha256": promo.shared._sha256(output),
                    },
                },
                "evaluation_sha256": "A" * 64,
            }
            with (
                mock.patch.object(promo.shared, "preflight_video_sources"),
                mock.patch.object(promo, "prepare_subtitle_layouts"),
                mock.patch.object(
                    promo.visual_audit,
                    "verify_report",
                    return_value=verified_audit,
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                release, release_chapters = validator.validate_project(
                    output,
                    stage="release",
                    visual_audit_report=audit_report,
                    expected_audit_sha256=audit_sha,
                )
            self.assertEqual(0, release["_placeholder_count"])
            self.assertEqual(20, len(release_chapters))

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
            for row in timeline["marks"]:
                if row["label"] == "policy_card_361_clean_end":
                    row["label"] = "policy_card_361_visible"
            _write_json(timeline_path, timeline)
            # An ordinary visible mark at the exact same timestamp cannot stand
            # in for an explicit clean boundary. Update only the index hash; the
            # report still carries the original timeline as an additional drift.
            _refresh_index_records(green, timeline_path)
            with self.assertRaisesRegex(prepare.PrepareError, "missing marks"):
                prepare.project_manifest(artifact_root=green)

    def test_red_or_unproven_clean_frame_gate_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for field, value, expected in (
                ("result", "RED", "is not GREEN"),
                (
                    "native_decisions_drawer_absent",
                    False,
                    "native_decisions_drawer_absent=true",
                ),
            ):
                with self.subTest(field=field):
                    capture = _make_capture(root / f"bad-gate-{field}")
                    timeline_path = (
                        capture / "cell" / "promo" / "capture-timeline.json"
                    )
                    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
                    gate = next(
                        row
                        for row in timeline["clean_frame_gates"]
                        if row["span_id"] == "jingcha_mandate"
                    )
                    gate[field] = value
                    _write_json(timeline_path, timeline)
                    _refresh_index_records(capture, timeline_path)
                    with self.assertRaisesRegex(prepare.PrepareError, expected):
                        prepare.project_manifest(artifact_root=capture)

    def test_clean_gate_requires_indexed_begin_end_frame_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missing_frames = _make_capture(root / "missing-gate-frames")
            timeline_path = (
                missing_frames / "cell" / "promo" / "capture-timeline.json"
            )
            timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
            timeline["clean_frame_gates"][0].pop("frames")
            _write_json(timeline_path, timeline)
            _refresh_index_records(missing_frames, timeline_path)
            with self.assertRaisesRegex(prepare.PrepareError, "begin/end frame proofs"):
                prepare.project_manifest(artifact_root=missing_frames)

            missing_index = _make_capture(root / "missing-gate-index")
            timeline = json.loads(
                (missing_index / "cell" / "promo" / "capture-timeline.json").read_text(
                    encoding="utf-8"
                )
            )
            gate_path = Path(
                timeline["clean_frame_gates"][0]["frames"][0]["gate"]["path"]
            )
            relative = gate_path.relative_to(missing_index).as_posix()
            index_path = missing_index / "evidence-index.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["files"] = [
                row for row in index["files"] if row["path"] != relative
            ]
            _write_json(index_path, index)
            with self.assertRaisesRegex(prepare.PrepareError, "evidence index is missing"):
                prepare.project_manifest(artifact_root=missing_index)

    def test_real_character_provenance_is_exact_and_report_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missing = _make_capture(root / "missing-real-character")
            timeline_path = missing / "cell" / "promo" / "capture-timeline.json"
            report_path = missing / "report.json"
            timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
            timeline["real_character_provenance"]["subjects"] = [
                row
                for row in timeline["real_character_provenance"]["subjects"]
                if row["history_id"] != "han_5253"
            ]
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["cell"]["promo_capture"] = copy.deepcopy(timeline)
            _write_json(timeline_path, timeline)
            _write_json(report_path, report)
            _refresh_index_records(missing, timeline_path, report_path)
            with self.assertRaisesRegex(
                prepare.PrepareError, "exactly Zhao Shu and one resolved"
            ):
                prepare.project_manifest(artifact_root=missing)

            drift = _make_capture(root / "report-provenance-drift")
            report_path = drift / "report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["cell"]["promo_capture"]["real_character_provenance"][
                "subjects"
            ][1]["display_name"] = "测试临时角色"
            _write_json(report_path, report)
            _refresh_index_records(drift, report_path)
            with self.assertRaisesRegex(prepare.PrepareError, "does not match"):
                prepare.project_manifest(artifact_root=drift)

            scenario_drift = _make_capture(root / "scenario-subject-drift")
            report_path = scenario_drift / "report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["cell"]["scenario_evidence"][
                "reviewed_official_history_id"
            ] = "han_6875"
            _write_json(report_path, report)
            _refresh_index_records(scenario_drift, report_path)
            with self.assertRaisesRegex(
                prepare.PrepareError, "exact reviewed official"
            ):
                prepare.project_manifest(artifact_root=scenario_drift)

    def test_real_character_provenance_accepts_one_resolved_duke_plus_tail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            capture = _make_capture(
                Path(temporary) / "dynamic-real-character",
                reviewed_history_id="han_6875",
            )
            manifest, _provenance = prepare.project_manifest(artifact_root=capture)
            real = manifest["release_manifest_provenance"][
                "real_character_provenance"
            ]
            self.assertEqual(
                ["han_8052", "han_6875"],
                [row["history_id"] for row in real["subjects"]],
            )
            self.assertEqual("唐介", real["subjects"][1]["display_name"])
            self.assertEqual(
                "k_hedong",
                real["title_history_assertions"][
                    "reviewed_official_title_at_start"
                ],
            )
            self.assertEqual(
                "h_china",
                real["title_history_assertions"][
                    "reviewed_official_title_liege_at_start"
                ],
            )

    def test_assessed_only_historical_count_cannot_be_promo_manager_subject(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "outside the frozen allowlist"):
                _make_capture(
                    Path(temporary) / "assessed-only-count",
                    reviewed_history_id="han_7247",
                )

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
