"""Small offline producer checks. Synthetic fixtures never form a GREEN CK3 bundle."""
import argparse
from datetime import datetime, timezone
import io
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from war_ai_promo import gameplay_bundle as gb
from war_ai_promo.common import binding, load, write_new
from war_ai_promo.capture_timing import TIMING_POLICY, analyze_timestamps, display_sampling

OUTPUT = None


class GameplayBundleOfflineTests(unittest.TestCase):
    def setUp(self):
        self.root = OUTPUT / self._testMethodName
        self.root.mkdir()

    def test_incomplete_recording_cannot_extract_or_package(self):
        source = self.root / "incomplete"
        source.mkdir()
        (source / "gameplay.mkv").write_bytes(b"synthetic incomplete recording")
        target = self.root / "must-not-exist"
        with self.assertRaisesRegex(gb.GameplayBundleError, "incomplete"):
            gb.extract_frames(source, target, 0, 1)
        with self.assertRaisesRegex(gb.GameplayBundleError, "incomplete"):
            gb.package_gameplay_bundle(source, self.root / "not-a-review.json", target, Path(__file__))
        self.assertFalse(target.exists())

    def test_claimed_human_signoff_is_not_accepted_as_image_review(self):
        review = {"schema": gb.REVIEW_SCHEMA, "reviewer": {"kind": "agent", "id": "synthetic-test"},
            "reviewed_at_utc": "2026-09-23T01:00:00+00:00",
            "review_scope": "endpoint-images-and-sampled-foreground", **gb.BOUNDARIES}
        review["signoff_granted"] = True
        path = self.root / "invalid-review.json"
        write_new(path, review)
        with self.assertRaisesRegex(gb.GameplayBundleError, "boundaries"):
            gb._review(path, {"recording_completed_at": "2026-09-23T00:00:00+00:00"})

    def test_extract_is_pending_and_keeps_exclusive_end_frame(self):
        source = self.root / "synthetic-source"
        source.mkdir()
        raw = source / "synthetic.bin"
        raw.write_bytes(b"not a CK3 recording; test injects completed-recording metadata")
        write_new(source / "recording-result.json", {"synthetic": True, "not_a_completion_receipt": True})
        state = {"root": source, "raw": binding(raw), "duration_seconds": 2,
            "resolution": [2, 2]}
        probe = self.root / "synthetic-frame-probe.json"
        write_new(probe, {"schema": gb.FRAME_PROBE_SCHEMA, "source_recording": binding(raw),
            "stream": {"time_base": "1/1000"}, "decoded_frame_count": 3,
            "capture_media_compatible": True, "capture_media_timing_policy": TIMING_POLICY,
            "sampling_quality": {"classification": "timestamped-non-CFR30"},
            "supported_end_seconds": 1.0, "audit_files": [], "frames": [
                {"decoded_index": 0, "pts": 0, "pts_seconds": 0},
                {"decoded_index": 1, "pts": 33, "pts_seconds": 0.033},
                {"decoded_index": 2, "pts": 967, "pts_seconds": 0.967}]})
        def fake_media(command, audit_directory):
            audit_directory.mkdir()
            write_new(audit_directory / "command.json", {"synthetic": True, "executed": False,
                "argv": list(command.argv)})
            Image.new("RGB", (2, 2), "red").save(command.argv[-1])
            return SimpleNamespace(returncode=0)
        target = self.root / "pending-extraction"
        with patch.object(gb, "completed_recording", return_value=state), patch.object(gb, "run_command", side_effect=fake_media) as media:
            result = gb.extract_frames(source, target, 0.03, 1, frame_probe=probe)
            self.assertEqual(media.call_count, 2)
            with self.assertRaises(FileExistsError):
                gb.extract_frames(source, target, 0.03, 1, frame_probe=probe)
        self.assertEqual(result["status"], "pending-agent-image-review")
        receipt = load(result["extraction"]["path"])
        self.assertEqual([row["decoded_index"] for row in receipt["frames"]], [1, 2])
        self.assertEqual([row["pts"] for row in receipt["frames"]], [33, 967])
        self.assertEqual(receipt["frames"][0]["command_argv"][receipt["frames"][0]["command_argv"].index("-vf")+1], "select=eq(pts\\,33)")
        self.assertTrue(receipt["capture_media_compatible"])
        self.assertEqual(receipt["capture_media_timing_policy"], TIMING_POLICY)
        self.assertFalse(receipt["signoff_granted"])
        self.assertFalse((target / "report.json").exists())
        with patch.object(gb, "completed_recording", return_value=state), patch.object(gb, "run_command", return_value=SimpleNamespace(returncode=0)):
            with self.assertRaisesRegex(gb.GameplayBundleError, "without an endpoint PNG"):
                gb.extract_frames(source, self.root / "zero-exit-no-image", 0.03, 1, frame_probe=probe)

    def test_actual_pts_override_nominal_30fps_metadata(self):
        raw = self.root / "synthetic-source.bin"
        raw.write_bytes(b"synthetic frame-probe fixture; no actual media")
        payload = {"streams": [{"time_base": "1/1000", "r_frame_rate": "30/1", "avg_frame_rate": "30/1"}],
            "format": {"duration": "0.233"}, "frames": [
                {"pts": 0, "pts_time": "0.000"}, {"pts": 100, "pts_time": "0.100"},
                {"pts": 200, "pts_time": "0.200"}]}
        import json
        with patch.object(gb, "run_command", return_value=SimpleNamespace(stdout=json.dumps(payload))):
            result = gb.probe_frame_timestamps(raw, self.root / "synthetic-timing-report")
        self.assertTrue(result["capture_media_compatible"])
        self.assertEqual(result["decoded_frame_count"], 3)
        report = load(result["report"]["path"])
        self.assertFalse(report["contiguous_zero_based_30fps"])
        self.assertAlmostEqual(report["maximum_gap_seconds"], 0.1)
        self.assertEqual(report["supported_end_seconds"], 0.2)
        self.assertFalse(report["sampling_quality"]["absence_of_behavior_between_samples_proven"])

    def test_gfxcapture_requires_the_verified_window(self):
        argv = ["ffmpeg", "-f", "lavfi", "-i", "gfxcapture=hwnd=462536:capture_cursor=0", "-vf", "hwdownload,format=bgra", "gameplay.mkv"]
        self.assertTrue(gb._recording_input_matches(argv, {"hwnd": 462536}))
        self.assertFalse(gb._recording_input_matches(argv, {"hwnd": 111}))
        self.assertFalse(gb._recording_input_matches(["gfxcapture=monitor_idx=0"], {"hwnd": 462536}))

    def test_bad_pts_and_unsupported_tail_are_not_filled(self):
        payload = {"streams": [{"time_base": "1/1000"}], "format": {"duration": "1"},
            "frames": [{"pts": 0, "pts_time": "0"}, {"pts": 100, "pts_time": "0.1"}]}
        facts = {"schema": gb.FRAME_PROBE_SCHEMA, **analyze_timestamps(payload)}
        window = {"output_grid_first_frame": 0, "output_grid_stop_frame_exclusive": 9, "expected_frame_count": 9}
        with self.assertRaisesRegex(ValueError, "support"):
            display_sampling(facts, window, 0)
        payload["frames"][1] = {"pts": 0, "pts_time": "0"}
        with self.assertRaisesRegex(ValueError, "increasing"):
            analyze_timestamps(payload)

    def test_sampling_uses_current_frame_and_retains_long_gap(self):
        payload = {"streams": [{"time_base": "1/1000"}], "format": {"duration": "1"},
            "frames": [{"pts": 0, "pts_time": "0"}, {"pts": 150, "pts_time": "0.15"},
                       {"pts": 900, "pts_time": "0.9", "duration": 100}]}
        facts = {"schema": gb.FRAME_PROBE_SCHEMA, **analyze_timestamps(payload)}
        window = {"output_grid_first_frame": 0, "output_grid_stop_frame_exclusive": 30, "expected_frame_count": 30}
        sample = display_sampling(facts, window, 0)
        self.assertEqual(sample["mapping"][4]["source_pts"], 0)  # t=.133 < .150
        self.assertEqual(sample["mapping"][5]["source_pts"], 150)
        self.assertEqual(sample["distinct_source_frames_displayed"], 3)
        self.assertAlmostEqual(sample["maximum_selected_gap_seconds"], .75)
        self.assertFalse(sample["tail_padding"])
        # A new first frame cannot be copied backwards to fill a missing start.
        facts["frames"] = facts["frames"][1:]
        with self.assertRaisesRegex(ValueError, "support"):
            display_sampling(facts, window, 0)


def main():
    global OUTPUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    OUTPUT = args.output.resolve()
    OUTPUT.mkdir(parents=True, exist_ok=False)
    capture = io.StringIO()
    result = unittest.TextTestRunner(stream=capture, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(GameplayBundleOfflineTests))
    text = capture.getvalue()
    (OUTPUT / "unittest.txt").write_bytes(text.encode("utf-8"))
    write_new(OUTPUT / "verification-index.json", {"status": "PASS" if result.wasSuccessful() else "FAIL",
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "tests": result.testsRun,
        "scope": "offline guard checks and synthetic pending-extraction shape only",
        "real_ck3_launched": False, "real_media_process_executed": False,
        "green_capture_bundle_created": False, "human_review_or_approval_created": False,
        "implementation": binding(gb.__file__), "tests_source": binding(__file__),
        "test_log": binding(OUTPUT / "unittest.txt")})
    print(text)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
