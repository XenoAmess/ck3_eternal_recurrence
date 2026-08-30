#!/usr/bin/env python3
"""Deterministic real-video tests for promo visual-audit evidence production."""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


TOOLS_DIRECTORY = Path(__file__).resolve().parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import audit_promo_visuals as audit  # noqa: E402
import prepare_promo_visual_audit as prepare  # noqa: E402


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


def _media_program(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} is required for promo evidence producer tests")
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


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def _real_video(path: Path) -> None:
    """Encode a short, genuinely decodable video with OCR-readable text."""

    source = path.with_suffix(".source.png")
    source.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (640, 360), (20, 35, 55))
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 92, 616, 246), outline=(198, 163, 78), width=4)
    draw.text(
        (43, 137),
        "CLEAN PRODUCT UI",
        font=_font(52),
        fill=(255, 255, 255),
    )
    image.save(source, format="PNG")
    _run_media(
        [
            _media_program("ffmpeg"),
            "-y",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-i",
            str(source),
            "-t",
            "2.2",
            "-r",
            "10",
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


def _fixture(root: Path) -> Path:
    history = root / "game" / "history" / "characters" / "han.txt"
    history.parent.mkdir(parents=True)
    history.write_text(
        "han_8052 = {\n\tname = Zhao_Shu\n}\n"
        "han_5253 = {\n\tname = Lu_Jujian\n}\n",
        encoding="utf-8",
    )
    video = root / "capture" / "clean-real-take.mkv"
    _real_video(video)
    history_record = _record(history, "exact-build CK3 history source")
    source_record = _record(video, "clean real-video fixture")
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
                "id": "00-generated",
                "type": "title_card",
                "material_status": "generated",
            },
            {
                "id": "01-manager-view",
                "type": "video_clip",
                "material_status": "captured",
                "source": source_record,
                "start_seconds": 0.0,
                "end_seconds": 1.0,
                "capture": {"clean_span_id": "managed_scoreboard"},
            },
            {
                "id": "02-received-view",
                "type": "video_clip",
                "material_status": "captured",
                "source": source_record,
                "start_seconds": 1.0,
                "end_seconds": 2.0,
                "capture": {"clean_span_id": "received_scoreboard_with_325"},
            },
        ],
    }
    manifest_path = root / "release-manifest.json"
    _write_json(manifest_path, manifest)
    return manifest_path


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _evidence_contract(spec: dict[str, object]) -> list[tuple[object, ...]]:
    return [
        (
            row["evidence_id"],
            tuple(row["chapter_ids"]),
            row.get("timestamp_seconds"),
            row["image"]["sha256"],
            row["ocr"]["sha256"],
        )
        for row in spec["evidence"]
    ]


class PromoVisualAuditProducerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _media_program("ffmpeg")
        _media_program("ffprobe")
        cls.ocr_engine = prepare._ocr_engine()

    def test_real_video_endpoints_merge_ocr_hashes_and_pending_signoff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = _fixture(root)
            spec_path, run_path, run = prepare.generate_pending_spec(
                release_manifest=manifest,
                output_directory=root / "external-process-output",
                sampling_interval_seconds=0.5,
                engine=self.ocr_engine,
            )
            spec = _load(spec_path)

            self.assertEqual(
                "EVIDENCE_READY_MANUAL_REVIEW_PENDING", run["result"]
            )
            self.assertEqual(5, run["video_frame_count"])
            self.assertEqual(5, run["evidence_count"])
            self.assertTrue(run_path.is_file())
            self.assertEqual(
                {
                    "emperor": ["han_8052"],
                    "hunan_governor": ["han_5253"],
                    "manager": ["han_8052"],
                    "reviewed_official": ["han_5253"],
                },
                spec["subject_role_map"],
            )
            self.assertEqual("PENDING", spec["manual_signoff"]["status"])
            self.assertEqual([], spec["manual_signoff"]["reviewed_chapter_ids"])
            self.assertEqual(
                {False}, set(spec["manual_signoff"]["attestations"].values())
            )
            self.assertEqual(
                [0.0, 0.5, 1.0],
                spec["generation"]["chapter_sample_timestamps_seconds"][
                    "01-manager-view"
                ],
            )
            self.assertEqual(
                [1.0, 1.5, 2.0],
                spec["generation"]["chapter_sample_timestamps_seconds"][
                    "02-received-view"
                ],
            )
            shared_endpoint = next(
                row
                for row in spec["evidence"]
                if row["timestamp_seconds"] == 1.0
            )
            self.assertEqual(
                ["01-manager-view", "02-received-view"],
                shared_endpoint["chapter_ids"],
            )
            self.assertEqual(
                ["han_5253", "han_8052"], shared_endpoint["subject_ids"]
            )
            manager_only = next(
                row
                for row in spec["evidence"]
                if row["timestamp_seconds"] == 0.5
            )
            reviewed_only = next(
                row
                for row in spec["evidence"]
                if row["timestamp_seconds"] == 1.5
            )
            self.assertEqual(["han_8052"], manager_only["subject_ids"])
            self.assertEqual(["han_5253"], reviewed_only["subject_ids"])
            for row in spec["evidence"]:
                image_path = Path(row["image"]["path"])
                ocr_path = Path(row["ocr"]["path"])
                ocr = _load(ocr_path)
                self.assertEqual(
                    audit.sha256_file(image_path), ocr["image_sha256"]
                )
                self.assertTrue(ocr["items"])
                self.assertEqual([0, 0, 640, 360], row["ocr_region"])

            # The producer is incapable of silently yielding a publishable
            # GREEN report.  Its untouched PENDING template must stay RED.
            pending_report = audit.create_report(spec_path)
            self.assertEqual("RED", pending_report["evaluation"]["result"])
            self.assertTrue(
                all(
                    "manual" in error
                    for error in pending_report["evaluation"]["errors"]
                )
            )

            # Simulate the separately preserved post-review document in this
            # fixture test.  The normal consumer then independently re-extracts
            # every real-video frame and validates pixel/hash/OCR bindings.
            signed = copy.deepcopy(spec)
            signed["manual_signoff"] = {
                "status": "GREEN",
                "reviewer": "fixture-human-reviewer",
                "reviewed_at_utc": "2026-08-29T16:00:00+08:00",
                "manifest_sha256": audit.sha256_file(manifest),
                "reviewed_chapter_ids": [
                    "01-manager-view",
                    "02-received-view",
                ],
                "attestations": {
                    key: True for key in audit.REQUIRED_ATTESTATIONS
                },
            }
            signed_path = root / "external-process-output" / "signed-spec.json"
            _write_json(signed_path, signed)
            signed_report = audit.create_report(signed_path)
            self.assertEqual("GREEN", signed_report["evaluation"]["result"])
            self.assertEqual([], signed_report["evaluation"]["findings"])

    def test_real_video_output_contract_is_deterministic_and_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = _fixture(root)
            first, _first_run, _ = prepare.generate_pending_spec(
                release_manifest=manifest,
                output_directory=root / "output-a",
                sampling_interval_seconds=0.5,
                engine=self.ocr_engine,
            )
            second, _second_run, _ = prepare.generate_pending_spec(
                release_manifest=manifest,
                output_directory=root / "output-b",
                sampling_interval_seconds=0.5,
                engine=self.ocr_engine,
            )
            first_payload = _load(first)
            second_payload = _load(second)
            self.assertEqual(
                _evidence_contract(first_payload),
                _evidence_contract(second_payload),
            )
            self.assertEqual(
                first_payload["generation"]["chapter_sample_timestamps_seconds"],
                second_payload["generation"]["chapter_sample_timestamps_seconds"],
            )
            for left, right in zip(
                first_payload["evidence"], second_payload["evidence"]
            ):
                self.assertEqual(
                    Path(left["ocr"]["path"]).read_bytes(),
                    Path(right["ocr"]["path"]).read_bytes(),
                )
            with self.assertRaisesRegex(
                prepare.PrepareVisualAuditError, "refusing to overwrite"
            ):
                prepare.generate_pending_spec(
                    release_manifest=manifest,
                    output_directory=root / "output-a",
                    sampling_interval_seconds=0.5,
                    engine=self.ocr_engine,
                )

    def test_sampling_contract_rejects_invalid_or_collapsed_intervals(self) -> None:
        self.assertEqual(
            (10.25, 11.25, 12.25, 12.4),
            prepare.sample_timestamps(10.25, 12.4, 1.0),
        )
        for values in (
            (0.0, 1.0, 0.0),
            (0.0, 1.0, 1.01),
            (1.0, 1.0, 0.5),
            (0.0000001, 0.0000002, 0.5),
        ):
            with self.subTest(values=values):
                with self.assertRaises(prepare.PrepareVisualAuditError):
                    prepare.sample_timestamps(*values)


if __name__ == "__main__":
    unittest.main()
