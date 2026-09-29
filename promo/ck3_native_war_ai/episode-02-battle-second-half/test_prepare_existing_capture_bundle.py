"""Fixture gates for the two-stage external CK3 capture bundle producer."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import prepare_existing_capture_bundle as bundle


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


class ExistingCaptureBundleTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.attempt = self.root / "source-live-a01"
        self.recorder = self.attempt / "recording-a01"
        self.recorder.mkdir(parents=True)
        self.output = self.root / "pending-a01"
        write(self.attempt / "ck3-output/capture-report.json", {
            "result": "ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO",
            "environment_session_complete": True, "adapter_bundle_validated": False,
            "worker": {"ok": True}, "cleanup_process_inventory": {"processes": []}})
        write(self.attempt / "ck3-output/session-result.json", {
            "ok": True, "shutdown": {"ok": True, "tree_gone": True,
                                     "cleanup_proven": True}})
        raw = self.recorder / "raw/take.mkv"
        raw.parent.mkdir()
        raw.write_bytes(b"fixture raw bytes")
        probe = self.recorder / "ffprobe.json"
        self.pts = ["0.000", "0.033", "0.066", "0.100"]
        write(probe, {"streams": [{"index": 0, "codec_type": "video"}],
                      "frames": [{"stream_index": 0, "best_effort_timestamp_time": value}
                                 for value in self.pts]})
        screen = self.recorder / "screens/one.png"
        screen.parent.mkdir()
        screen.write_bytes(b"original screenshot")
        control = self.attempt / "ck3-output/interactive-requests-responses/control.json"
        write(control, {"result": "CALL_COMPLETED"})
        marks = self.recorder / "marks.jsonl"
        rows = [{"kind": "recorder-start", "monotonic_ns": 100},
                {"kind": "day-visible", "monotonic_ns": 200,
                 "approx_seconds_from_recorder_start": 0.05,
                 "approx_seconds_are_not_video_pts": True,
                 "date_raw": 53146992, "combat_id": 16777218, "war_id": 4,
                 "control": bundle.record(control), "screenshot": bundle.record(screen)},
                {"kind": "recorder-end", "monotonic_ns": 300}]
        marks.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        write(self.recorder / "recorder-intent.json", {
            "raw_path": str(raw), "session_output": str(self.attempt / "ck3-output")})
        write(self.recorder / "recorder-start.json", {"monotonic_ns": 100})
        write(self.recorder / "recorder-end.json", {
            "monotonic_ns": 300, "elapsed_monotonic_seconds": 0.12,
            "ended_at": "2026-09-28T10:00:00+00:00",
            "ffmpeg_exit_code": 0, "interrupted": False, "raw": bundle.record(raw)})
        write(self.recorder / "ffprobe-command.json", ["ffprobe", str(raw)])
        write(self.recorder / "geometry-admission.json", {"valid_and_equal": True})
        (self.recorder / "ffmpeg.stderr.txt").write_bytes(b"")
        write(self.recorder / "recorder-final.json", {
            "result": "ENCODED_UNREVIEWED", "clean_spans_certified": False,
            "human_review_completed": False, "ffmpeg_exit_code": 0, "ffprobe_exit_code": 0,
            "video_pts_complete": True, "raw": bundle.record(raw),
            "ffprobe_output": bundle.record(probe), "marks": bundle.record(marks),
            "frame_pts_by_stream": {"0": {"count": len(self.pts)}},
            "format_duration_seconds": "0.120"})
        self.raw = raw

    def add_sibling_screenshot_mark(self, screenshot: Path, *, key: str = "screenshot") -> None:
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        screenshot.write_bytes(b"preserved original screen lease screenshot")
        marks = self.recorder / "marks.jsonl"
        rows = [json.loads(line) for line in marks.read_text(encoding="utf-8").splitlines()]
        rows.insert(-1, {"kind": "next-day-visible", "monotonic_ns": 250,
                         "approx_seconds_from_recorder_start": 0.08,
                         "approx_seconds_are_not_video_pts": True,
                         "date_raw": 53147016, "combat_id": 16777218, "war_id": 4,
                         key: bundle.record(screenshot)})
        marks.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        final_path = self.recorder / "recorder-final.json"
        final = bundle.read_json(final_path)
        final["marks"] = bundle.record(marks)
        write(final_path, final)

    def prepare(self) -> dict:
        with patch.object(bundle, "toolchain_identity", return_value={
            "version": "0.2.1", "release_tag": "v0.2.1",
            "wheel_sha256": "F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621",
            "wheel_url": "https://github.com/XenoAmess/xar_promo_toolchain/releases/download/v0.2.1/xar_promo_toolchain-0.2.1-py3-none-any.whl"}):
            bundle.prepare(self.attempt, self.recorder, self.output, self.root / "unused.txt")
        return bundle.read_json(self.output / "source-manifest.json")

    def review(self, source: dict, *, end_pts: str = "0.100") -> Path:
        frames = {}
        for phase, pts in (("begin", "0.033"), ("end", end_pts)):
            image = self.root / f"{phase}.png"
            image.write_bytes(f"raw-derived {phase} frame".encode())
            index = ("0.000", "0.033", "0.066", end_pts).index(pts)
            command = self.root / f"{phase}-command.json"
            write(command, {"argv": ["fixture-ffmpeg", *bundle.extract_argv_tail(
                                      source["raw"]["path"], index, str(image))],
                            "source_manifest": bundle.record(self.output / "source-manifest.json"),
                            "ffprobe": source["ffprobe"], "selected_decoded_index": index,
                            "requested_pts_seconds": pts})
            stdout = self.root / f"{phase}-stdout.bin"
            stdout.write_bytes(b"")
            stderr = self.root / f"{phase}-stderr.txt"
            stderr.write_text(f"pts_time:{pts}\n", encoding="utf-8")
            extraction = self.root / f"{phase}-extraction.json"
            write(extraction, {"result": "EXTRACTED_UNREVIEWED",
                               "created_at_utc": "2026-09-28T10:30:00+00:00",
                               "raw": source["raw"],
                               "image": bundle.record(image), "pts_seconds": pts,
                               "ffprobe": source["ffprobe"], "decoded_index": index,
                               "command": bundle.record(command), "stdout": bundle.record(stdout),
                               "stderr": bundle.record(stderr), "human_review_performed": False})
            frames[f"{phase}_frame"] = {"pts_seconds": pts, "image": bundle.record(image),
                                           "extraction_receipt": bundle.record(extraction),
                                           "reviewed_at_1x": True, "gameplay_hud": True,
                                           "source_identity_visible": True, "no_loading": True}
        review = self.root / "human-review.json"
        write(review, {"schema": bundle.REVIEW_SCHEMA,
                       "reviewer": {"kind": "human", "id": "fixture reviewer"},
                       "reviewed_at_utc": "2026-09-28T11:00:00+00:00",
                       "review_scope": "full_raw_1x_and_exact_span_endpoints",
                       "human_1x_full_raw_review_performed": True,
                       "gameplay_hud_visible_at_recording_start": True,
                       "loading_excluded_from_selected_spans": True,
                       "source_manifest": bundle.record(self.output / "source-manifest.json"),
                       "raw": source["raw"],
                       "spans": [{"span_id": "terminal_window", "begin_pts_seconds": "0.033",
                                  "end_pts_seconds": end_pts,
                                  "continuous_visual_review_performed": True,
                                  "source_identity_visible_and_checked": True,
                                  "no_foreign_overlay": True, **frames}]})
        return review

    def test_pending_inventory_does_not_create_adapter_green(self) -> None:
        source = self.prepare()
        self.assertEqual(source["status"], "PENDING_CLEAN_REVIEW")
        self.assertFalse(source["adapter_eligible"])
        self.assertIsNone(source["navigation_marks"][0]["media_pts_seconds"])
        self.assertEqual(source["navigation_marks"][0]["wall_clock_navigation_seconds"], "0.05")
        self.assertFalse((self.output / "report.json").exists())
        self.assertFalse((self.output / "evidence-index.json").exists())
        self.assertTrue(self.raw.exists())

    def test_matching_screen_lease_screenshot_survives_prepare_and_package(self) -> None:
        screenshot = self.root / "source-screen-lease-a01/d06-hover.png"
        self.add_sibling_screenshot_mark(screenshot)
        original = bundle.record(screenshot)
        source = self.prepare()
        bundle.validate_source_inventory(source)
        self.assertIn(original, source["files"])
        self.assertEqual(source["navigation_marks"][1]["evidence"]["screenshot"], original)
        review = self.review(source)
        result = bundle.package(self.output / "source-manifest.json", review,
                                self.root / "bundle-screen-lease")
        self.assertEqual(result["status"], "ADAPTER_VALIDATED_SELECTED_SPANS_ONLY")
        copied = (self.root / "bundle-screen-lease/source/external-screen-lease"
                  / "source-screen-lease-a01/d06-hover.png")
        self.assertEqual(bundle.record(copied)["sha256"], original["sha256"])
        self.assertEqual(bundle.record(screenshot), original)

    def test_unrelated_sibling_screenshot_is_rejected_before_pending_inventory(self) -> None:
        self.add_sibling_screenshot_mark(self.root / "other-screen-lease-a01/d06-hover.png")
        with patch.object(bundle, "toolchain_identity", return_value={"version": "0.2.1"}):
            with self.assertRaisesRegex(ValueError, "evidence escapes source attempt"):
                bundle.prepare(self.attempt, self.recorder, self.output, self.root / "unused")
        self.assertFalse(self.output.exists())

    def test_matching_screen_lease_cannot_supply_control(self) -> None:
        self.add_sibling_screenshot_mark(self.root / "source-screen-lease-a01/control.png",
                                         key="control")
        with patch.object(bundle, "toolchain_identity", return_value={"version": "0.2.1"}):
            with self.assertRaisesRegex(ValueError, "evidence escapes source attempt"):
                bundle.prepare(self.attempt, self.recorder, self.output, self.root / "unused")
        self.assertFalse(self.output.exists())

    def test_exact_release_pin_matches_installed_toolchain(self) -> None:
        requirements = Path(__file__).resolve().parents[3] / "tools/requirements-promo-toolchain.txt"
        identity = bundle.toolchain_identity(requirements)
        self.assertEqual(identity["version"], "0.2.1")
        self.assertEqual(identity["wheel_sha256"],
                         "F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621")

    def test_exact_frame_extractor_binds_showinfo_pts_without_review(self) -> None:
        self.prepare()
        def fake_run(argv, **kwargs):
            self.assertEqual(argv[argv.index("-fps_mode") + 1], "passthrough")
            self.assertNotIn("-vsync", argv)
            Path(argv[-1]).write_bytes(b"raw-derived fixture frame")
            kwargs["stderr"].write(b"[Parsed_showinfo_1] n: 0 pts: 33 pts_time:0.033\n")
            return SimpleNamespace(returncode=0)
        with patch.object(bundle.shutil, "which", return_value="fixture-ffmpeg"), \
                patch.object(bundle.subprocess, "run", side_effect=fake_run):
            result = bundle.extract_frame(self.output / "source-manifest.json", "0.033",
                                          self.root / "exact-frame-a01")
        self.assertEqual(result["result"], "EXTRACTED_UNREVIEWED")
        self.assertFalse(result["human_review_performed"])
        self.assertEqual(result["pts_seconds"], "0.033")
        self.assertEqual(result["decoded_index"], 1)

    def test_exact_frame_extractor_records_absolute_image_when_output_relative(self) -> None:
        self.prepare()
        def fake_run(argv, **kwargs):
            self.assertTrue(Path(argv[-1]).is_absolute())
            Path(argv[-1]).write_bytes(b"frame")
            kwargs["stderr"].write(b"pts_time:0.033\n")
            return SimpleNamespace(returncode=0)
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            with patch.object(bundle.shutil, "which", return_value="fixture-ffmpeg"), \
                    patch.object(bundle.subprocess, "run", side_effect=fake_run):
                bundle.extract_frame(self.output / "source-manifest.json", "0.033",
                                     Path("relative-frame"))
        finally:
            os.chdir(previous)

    def test_explicit_review_packages_and_loads_adapter_bundle(self) -> None:
        source = self.prepare()
        review = self.review(source)
        result = bundle.package(self.output / "source-manifest.json", review, self.root / "bundle-a01")
        self.assertEqual(result["status"], "ADAPTER_VALIDATED_SELECTED_SPANS_ONLY")
        self.assertFalse(result["film_signoff_granted"])
        self.assertEqual(result["span_ids"], ["terminal_window"])
        self.assertEqual(bundle.read_json(self.attempt / "ck3-output/capture-report.json")["result"],
                         "ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO")

    def test_package_refuses_missing_human_attestation_without_writing(self) -> None:
        source = self.prepare()
        review = self.review(source)
        payload = bundle.read_json(review)
        payload["reviewer"]["kind"] = "agent"
        write(review, payload)
        target = self.root / "should-not-exist"
        with self.assertRaisesRegex(ValueError, "human 1x"):
            bundle.package(self.output / "source-manifest.json", review, target)
        self.assertFalse(target.exists())

    def test_package_refuses_pts_gap(self) -> None:
        probe = self.recorder / "ffprobe.json"
        values = bundle.read_json(probe)
        values["frames"][2]["best_effort_timestamp_time"] = "0.400"
        values["frames"][3]["best_effort_timestamp_time"] = "0.433"
        write(probe, values)
        final_path = self.recorder / "recorder-final.json"
        final = bundle.read_json(final_path)
        final["ffprobe_output"] = bundle.record(probe)
        final["format_duration_seconds"] = "0.500"
        write(final_path, final)
        source = self.prepare()
        review = self.review(source, end_pts="0.433")
        with self.assertRaisesRegex(ValueError, "raw PTS gap"):
            bundle.package(self.output / "source-manifest.json", review, self.root / "gap-bundle")
        self.assertFalse((self.root / "gap-bundle").exists())

    def test_forged_pending_manifest_cannot_package_green(self) -> None:
        source = self.prepare()
        source["files"] = [item for item in source["files"] if item["path"] != source["raw"]["path"]]
        manifest = self.output / "source-manifest.json"
        write(manifest, source)
        review = self.review(source)
        target = self.root / "forged-bundle"
        with self.assertRaisesRegex(ValueError, "missing or unexpected originals"):
            bundle.package(manifest, review, target)
        self.assertFalse(target.exists())

    def test_review_before_recording_end_cannot_package_green(self) -> None:
        source = self.prepare()
        review = self.review(source)
        payload = bundle.read_json(review)
        payload["reviewed_at_utc"] = "2026-09-28T09:59:00+00:00"
        write(review, payload)
        with self.assertRaisesRegex(ValueError, "must follow actual recorder end"):
            bundle.package(self.output / "source-manifest.json", review,
                           self.root / "early-review-bundle")

    def test_prepare_rejects_recorder_end_raw_mismatch(self) -> None:
        end_path = self.recorder / "recorder-end.json"
        end = bundle.read_json(end_path)
        end["raw"] = bundle.record(self.recorder / "ffprobe.json")
        write(end_path, end)
        with patch.object(bundle, "toolchain_identity", return_value={"version": "0.2.1"}):
            with self.assertRaisesRegex(ValueError, "recorder end raw differs"):
                bundle.prepare(self.attempt, self.recorder, self.output, self.root / "unused")
        self.assertFalse(self.output.exists())

    def test_package_rejects_extraction_from_other_video(self) -> None:
        source = self.prepare()
        review = self.review(source)
        payload = bundle.read_json(review)
        frame = payload["spans"][0]["begin_frame"]
        receipt_path = Path(frame["extraction_receipt"]["path"])
        receipt = bundle.read_json(receipt_path)
        command_path = Path(receipt["command"]["path"])
        command = bundle.read_json(command_path)
        command["argv"][command["argv"].index("-i") + 1] = "D:/unrelated-video.mkv"
        write(command_path, command)
        receipt["command"] = bundle.record(command_path)
        write(receipt_path, receipt)
        frame["extraction_receipt"] = bundle.record(receipt_path)
        write(review, payload)
        with self.assertRaisesRegex(ValueError, "command does not bind selected frame"):
            bundle.package(self.output / "source-manifest.json", review,
                           self.root / "wrong-video-bundle")

    def test_review_cannot_predate_exact_endpoint_extraction(self) -> None:
        source = self.prepare()
        review = self.review(source)
        payload = bundle.read_json(review)
        payload["reviewed_at_utc"] = "2026-09-28T10:15:00+00:00"
        write(review, payload)
        with self.assertRaisesRegex(ValueError, "precede review"):
            bundle.package(self.output / "source-manifest.json", review,
                           self.root / "premature-review-bundle")


if __name__ == "__main__":
    unittest.main()
