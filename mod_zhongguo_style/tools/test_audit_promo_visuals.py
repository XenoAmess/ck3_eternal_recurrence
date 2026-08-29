#!/usr/bin/env python3
"""Offline tests for the ZhongGuo clean promotional-visual gate."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


TOOLS_DIRECTORY = Path(__file__).resolve().parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import audit_promo_visuals as audit  # noqa: E402


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _record(path: Path, label: str) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "label": label,
        "bytes": path.stat().st_size,
        "sha256": audit.sha256_file(path),
    }


def _png(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 18), color).save(path, format="PNG")


def _media_program(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} is required for promo visual audit tests")
    return executable


def _run_media(command: list[str]) -> None:
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode != 0:
        raise RuntimeError(
            completed.stderr.decode("utf-8", errors="replace").strip()
        )


def _video(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _run_media(
        [
            _media_program("ffmpeg"),
            "-y",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=32x18:rate=10:duration=2",
            "-an",
            "-c:v",
            "ffv1",
            "-g",
            "1",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ]
    )


def _extract_frame(video: Path, timestamp: float, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    _run_media(
        [
            _media_program("ffmpeg"),
            "-y",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{timestamp:.6f}",
            "-i",
            str(video),
            "-map",
            "0:v:0",
            "-frames:v",
            "1",
            "-an",
            "-sn",
            "-dn",
            "-pix_fmt",
            "rgb24",
            str(output),
        ]
    )


def _ocr(path: Path, image: Path, texts: tuple[str, ...]) -> None:
    _write_json(
        path,
        {
            "image_sha256": audit.sha256_file(image),
            "items": [
                {"text": text, "bbox": [0, 0, 31, 17]} for text in texts
            ],
        },
    )


def _fixture(
    root: Path,
    *,
    video_times: tuple[float, ...] = (0.0, 0.5, 1.0),
    first_ocr: tuple[str, ...] = ("天朝官员考核榜",),
) -> Path:
    history = root / "game" / "history" / "characters" / "han.txt"
    history.parent.mkdir(parents=True)
    history.write_text(
        "han_8052 = {\n\tname = Zhao_Shu\n}\n"
        "han_5253 = {\n\tname = Lu_Jujian\n}\n",
        encoding="utf-8",
    )
    raw = root / "capture" / "clean-source.mkv"
    _video(raw)
    still = root / "capture" / "policy-361.png"
    _png(still, (24, 42, 64))
    history_record = _record(history, "exact-build CK3 history source")

    manifest = {
        "project_status": "captured_release_candidate",
        "release_manifest_provenance": {
            "capture_result": "GREEN",
            "real_character_provenance": {
                "schema_version": 1,
                "bookmark": {"id": "1066_song", "start_date": "1066.9.15"},
                "subjects": [
                    {
                        "history_id": "han_8052",
                        "display_name": "赵曙",
                        "roles": ["emperor", "manager"],
                        "origin": "ck3_history_database",
                        "temporary_or_generated": False,
                        "history_source": history_record,
                    },
                    {
                        "history_id": "han_5253",
                        "display_name": "吕居简",
                        "roles": ["hunan_governor", "reviewed_official"],
                        "origin": "ck3_history_database",
                        "temporary_or_generated": False,
                        "history_source": history_record,
                    },
                ],
            },
        },
        "chapters": [
            {
                "id": "00-opening",
                "type": "title_card",
                "material_status": "generated",
            },
            {
                "id": "01-live",
                "type": "video_clip",
                "material_status": "captured",
                "source": _record(raw, "clean raw"),
                "start_seconds": 0.0,
                "end_seconds": max(video_times),
                "capture": {"clean_span_id": "managed_scoreboard"},
            },
            {
                "id": "02-still",
                "type": "still",
                "material_status": "captured",
                "source": _record(still, "clean still"),
                "capture": {"clean_span_id": "policy_card_361"},
            },
        ],
    }
    manifest_path = root / "release-manifest.json"
    _write_json(manifest_path, manifest)

    evidence: list[dict[str, object]] = []
    for index, timestamp in enumerate(video_times):
        image = root / "evidence" / f"video-{index:02d}.png"
        ocr = root / "evidence" / f"video-{index:02d}.ocr.json"
        _extract_frame(raw, timestamp, image)
        _ocr(
            ocr,
            image,
            first_ocr if index == 0 else ("制度驾驶舱",),
        )
        evidence.append(
            {
                "evidence_id": f"video-{index:02d}",
                "chapter_ids": ["01-live"],
                "subject_ids": ["song-emperor"],
                "source_sha256": manifest["chapters"][1]["source"]["sha256"],
                "timestamp_seconds": timestamp,
                "image": _record(image, "full-screen extracted frame"),
                "ocr": _record(ocr, "full-screen OCR JSON"),
                "ocr_region": [0, 0, 32, 18],
            }
        )
    still_ocr = root / "evidence" / "still.ocr.json"
    _ocr(still_ocr, still, ("三六一绩效宪章",))
    evidence.append(
        {
            "evidence_id": "still-361",
            "chapter_ids": ["02-still"],
            "subject_ids": ["hunan-governor"],
            "source_sha256": manifest["chapters"][2]["source"]["sha256"],
            "image": _record(still, "exact manifest still"),
            "ocr": _record(still_ocr, "full-screen OCR JSON"),
            "ocr_region": [0, 0, 32, 18],
        }
    )

    spec = {
        "schema_version": 1,
        "kind": audit.SPEC_KIND,
        "release_manifest": _record(manifest_path, "captured release manifest"),
        "frame_geometry": {"width": 32, "height": 18},
        "sampling_interval_seconds": 0.5,
        "bookmark": {"id": "1066_song", "start_date": "1066.9.15"},
        "historical_characters": [
            {
                "subject_id": "song-emperor",
                "history_id": "han_8052",
                "display_name": "赵曙",
                "roles": ["manager", "emperor"],
                "origin": "ck3_history_database",
                "temporary_or_generated": False,
                "history_source": history_record,
            },
            {
                "subject_id": "hunan-governor",
                "history_id": "han_5253",
                "display_name": "吕居简",
                "roles": ["reviewed_official", "hunan_governor"],
                "origin": "ck3_history_database",
                "temporary_or_generated": False,
                "history_source": history_record,
            },
        ],
        "additional_forbidden_tokens": [],
        "evidence": evidence,
        "manual_signoff": {
            "status": "GREEN",
            "reviewer": "visual-reviewer",
            "reviewed_at_utc": "2026-08-29T14:00:00+08:00",
            "manifest_sha256": audit.sha256_file(manifest_path),
            "reviewed_chapter_ids": ["01-live", "02-still"],
            "attestations": {
                "historical_characters_only": True,
                "no_generated_official_name_visible": True,
                "fixture_test_ui_absent": True,
                "full_clip_reviewed": True,
                "no_crop_mask_or_redaction": True,
            },
        },
    }
    spec_path = root / "visual-audit-spec.json"
    _write_json(spec_path, spec)
    return spec_path


class PromoVisualAuditTests(unittest.TestCase):
    def test_green_report_binds_manifest_frames_ocr_history_and_signoff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = _fixture(root)
            output = root / "release" / "visual-audit.json"
            report, written = audit.write_report(spec, output)

            self.assertEqual("GREEN", report["evaluation"]["result"])
            self.assertEqual(4, report["evaluation"]["summary"]["full_screen_evidence_frames"])
            self.assertEqual(2, report["evaluation"]["summary"]["historical_characters"])
            self.assertEqual(
                {"ffv1"},
                {
                    row["probe"]["codec_name"]
                    for row in report["evaluation"]["video_sources"]
                },
            )
            self.assertEqual([], report["evaluation"]["findings"])
            verified = audit.verify_report(
                written, expected_sha256=audit.sha256_file(written)
            )
            self.assertEqual(report["evaluation_sha256"], verified["evaluation_sha256"])
            with self.assertRaisesRegex(audit.AuditError, "refusing to overwrite"):
                audit.write_report(spec, output)

    def test_split_fixture_phrase_in_full_screen_ocr_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec = _fixture(
                Path(temporary),
                first_ocr=("验收上司", "给我的绩效"),
            )
            report = audit.create_report(spec)
            evaluation = report["evaluation"]
            self.assertEqual("RED", evaluation["result"])
            self.assertEqual(
                ["验收上司给我的绩效"],
                evaluation["evidence"][0]["forbidden_hits"],
            )
            self.assertIn("forbidden fixture/test-only text", evaluation["errors"][-1])

    def test_generated_character_or_missing_history_key_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec_path = _fixture(root)
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["historical_characters"][0]["temporary_or_generated"] = True
            _write_json(spec_path, spec)
            report = audit.create_report(spec_path)
            self.assertEqual("RED", report["evaluation"]["result"])
            self.assertIn("temporary_or_generated must be false", report["evaluation"]["errors"][0])

            missing = root / "missing-history-spec.json"
            spec["historical_characters"][0]["temporary_or_generated"] = False
            spec["historical_characters"][0]["history_id"] = "han_missing"
            _write_json(missing, spec)
            report = audit.create_report(missing)
            self.assertEqual("RED", report["evaluation"]["result"])
            self.assertIn("absent from its bound CK3 history source", report["evaluation"]["errors"][0])

    def test_non_green_release_manifest_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec_path = _fixture(root)
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            manifest_path = root / "release-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["release_manifest_provenance"]["capture_result"] = "RED"
            _write_json(manifest_path, manifest)
            spec["release_manifest"] = _record(
                manifest_path, "RED release manifest"
            )
            _write_json(spec_path, spec)

            report = audit.create_report(spec_path)
            self.assertEqual("RED", report["evaluation"]["result"])
            self.assertIn("capture_result='GREEN'", report["evaluation"]["errors"][0])

    def test_video_sampling_gap_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec = _fixture(Path(temporary), video_times=(0.0, 1.5))
            report = audit.create_report(spec)
            self.assertEqual("RED", report["evaluation"]["result"])
            self.assertTrue(
                any("sampling gap" in row for row in report["evaluation"]["errors"])
            )

    def test_empty_ocr_is_not_accepted_as_visual_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec_path = _fixture(root)
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            ocr_path = root / "evidence" / "video-00.ocr.json"
            image_path = Path(spec["evidence"][0]["image"]["path"])
            _write_json(
                ocr_path,
                {
                    "image_sha256": audit.sha256_file(image_path),
                    "items": [],
                },
            )
            spec["evidence"][0]["ocr"] = _record(
                ocr_path, "empty full-screen OCR JSON"
            )
            _write_json(spec_path, spec)

            report = audit.create_report(spec_path)
            self.assertEqual("RED", report["evaluation"]["result"])
            self.assertIn("contains no text rows", report["evaluation"]["errors"][0])

    def test_video_evidence_png_must_match_bound_decoded_frame(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec_path = _fixture(root)
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            evidence = spec["evidence"][0]
            image_path = Path(evidence["image"]["path"])
            ocr_path = Path(evidence["ocr"]["path"])
            _png(image_path, (255, 0, 255))
            evidence["image"] = _record(image_path, "substituted full-screen PNG")
            ocr_payload = json.loads(ocr_path.read_text(encoding="utf-8"))
            ocr_payload["image_sha256"] = audit.sha256_file(image_path)
            _write_json(ocr_path, ocr_payload)
            evidence["ocr"] = _record(ocr_path, "OCR rebound to substituted PNG")
            _write_json(spec_path, spec)

            report = audit.create_report(spec_path)
            self.assertEqual("RED", report["evaluation"]["result"])
            self.assertIn(
                "image pixels do not match bound video frame",
                report["evaluation"]["errors"][0],
            )

    def test_still_ocr_sidecar_must_bind_exact_image_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec_path = _fixture(root)
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            evidence = spec["evidence"][-1]
            ocr_path = Path(evidence["ocr"]["path"])
            payload = json.loads(ocr_path.read_text(encoding="utf-8"))
            payload["image_sha256"] = "0" * 64
            _write_json(ocr_path, payload)
            evidence["ocr"] = _record(ocr_path, "OCR with wrong image binding")
            _write_json(spec_path, spec)

            report = audit.create_report(spec_path)
            self.assertEqual("RED", report["evaluation"]["result"])
            self.assertIn(
                "image_sha256 does not bind its submitted PNG",
                report["evaluation"]["errors"][0],
            )

    def test_audit_characters_must_exactly_match_manifest_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec_path = _fixture(root)
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["historical_characters"][0]["display_name"] = "伪赵曙"
            _write_json(spec_path, spec)

            report = audit.create_report(spec_path)
            self.assertEqual("RED", report["evaluation"]["result"])
            self.assertIn(
                "must exactly match release manifest real_character_provenance",
                report["evaluation"]["errors"][0],
            )
            self.assertIn("mismatched=['han_8052']", report["evaluation"]["errors"][0])

    def test_evidence_subject_cannot_be_swapped_across_historical_roles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec_path = _fixture(root)
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["evidence"][0]["subject_ids"] = ["hunan-governor"]
            _write_json(spec_path, spec)

            report = audit.create_report(spec_path)
            self.assertEqual("RED", report["evaluation"]["result"])
            self.assertIn(
                "subject_ids must exactly bind the clean-span historical roles",
                report["evaluation"]["errors"][0],
            )

    def test_bookmark_must_match_manifest_character_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec_path = _fixture(root)
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["bookmark"]["id"] = "unrelated_bookmark"
            _write_json(spec_path, spec)

            report = audit.create_report(spec_path)
            self.assertEqual("RED", report["evaluation"]["result"])
            self.assertIn(
                "bookmark must exactly match release manifest",
                report["evaluation"]["errors"][0],
            )

    def test_ffprobe_geometry_must_match_declared_full_screen_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec_path = _fixture(root)
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["frame_geometry"]["width"] = 31
            _write_json(spec_path, spec)

            report = audit.create_report(spec_path)
            self.assertEqual("RED", report["evaluation"]["result"])
            self.assertIn(
                "ffprobe video geometry does not match frame_geometry",
                report["evaluation"]["errors"][0],
            )

    def test_default_forbidden_tokens_are_runner_superset(self) -> None:
        runner_tokens = {
            "决议和大型工程",
            "361制实机验收",
            "开始361制实机验收",
            "验收上司给我的绩效",
            "验收免费京察规划器",
            "演示政策卡",
            "演示触发器",
            "切换至宋帝并开考",
            "切换受考",
            "发出京察召集令",
            "打开此卡",
            "ZhongGuo 361 live acceptance",
            "Verify My Superior's Rating",
            "Verify the Free Jingcha Planner",
            "Promo Policy Card",
            "Switch to Song and begin review",
            "Open this card",
            "ZGA",
            "zga_",
            "zga.",
        }
        self.assertLessEqual(runner_tokens, set(audit.DEFAULT_FORBIDDEN_TOKENS))

    def test_verify_rejects_evidence_mutated_after_green_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = _fixture(root)
            report_path = root / "visual-audit.json"
            audit.write_report(spec, report_path)
            ocr = root / "evidence" / "video-00.ocr.json"
            _write_json(
                ocr,
                {
                    "image_sha256": "0" * 64,
                    "items": [{"text": "演示政策卡 #001"}],
                },
            )
            with self.assertRaisesRegex(audit.AuditError, "byte count mismatch|SHA-256 mismatch"):
                audit.verify_report(report_path)


if __name__ == "__main__":
    unittest.main()
