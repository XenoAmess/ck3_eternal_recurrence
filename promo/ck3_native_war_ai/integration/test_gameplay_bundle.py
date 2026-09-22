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
            "capture_media_compatible": False, "audit_files": [], "frames": [
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
        self.assertFalse(receipt["capture_media_compatible"])
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
        self.assertFalse(result["capture_media_compatible"])
        self.assertEqual(result["decoded_frame_count"], 3)


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
