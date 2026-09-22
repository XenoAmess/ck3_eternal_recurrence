"""Synthetic-only capture importer checks; never manufacture a GREEN CK3 report.

The successful media test injects an explicitly synthetic CaptureBundle
projection. The actual adapter is exercised only for a real RED rejection.
All test assets and failures remain in the supplied new artifact directory.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from xar_promo.adapters.ck3 import CaptureBundle, CaptureFile, CaptureMark, CleanSpan, CK3CaptureError
from xar_promo.process import CommandSpec, run_command

from war_ai_promo import capture_media as cm
from war_ai_promo.common import binding, load, write_new


ARTIFACT_ROOT: Path
FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"


def capture_file(path: Path, root: Path) -> CaptureFile:
    info = binding(path)
    return CaptureFile(path.relative_to(root).as_posix(), path, info["bytes"], info["sha256"].upper())


class CaptureMediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle_root = ARTIFACT_ROOT / "synthetic-source"
        cls.bundle_root.mkdir()
        cls.raw = cls.bundle_root / "lavfi-testsrc.mp4"
        run_command(CommandSpec.create([
            FFMPEG, "-nostdin", "-hide_banner", "-loglevel", "warning", "-n",
            "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=2",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2",
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", cls.raw,
        ], label="synthetic importer test input, not CK3", partial_artifacts=[cls.raw]),
            audit_directory=ARTIFACT_ROOT / "synthetic-source-command")
        controls = []
        for name in ("synthetic-report.json", "synthetic-timeline.json", "synthetic-index.json", "synthetic-frame-proof.json"):
            path = cls.bundle_root / name
            write_new(path, {"synthetic": True, "adapter_projection_is_mocked": True,
                      "not_a_ck3_capture_report": True, "file": name})
            controls.append(capture_file(path, cls.bundle_root))
        span = CleanSpan("SYNTHETIC", "SYNTHETIC_clean_begin", "SYNTHETIC_clean_end", 0.0, 2.0, (controls[3],))
        cls.bundle = CaptureBundle(cls.bundle_root, "synthetic-test-only",
            "synthetic lavfi; mocked adapter projection; not CK3 footage",
            controls[0], controls[1], controls[2], capture_file(cls.raw, cls.bundle_root),
            (CaptureMark("recording_started_after_gameplay_hud",0),CaptureMark("recording_stop_requested",2)),
            (span,),0,2)
        cls.spec = {"cue_id":"TEST-CUE", "bundle_root":cls.bundle_root.as_posix(), "span_id":"SYNTHETIC",
                    "offset_seconds":0.2, "duration_seconds":0.8, "evidence_role":"context", "claim_ids":["TEST-NOT-A-CLAIM"]}
        write_new(ARTIFACT_ROOT / "test-scope.json", {
            "synthetic_only":True, "ck3_started":False, "real_green_bundle_tested":False,
            "successful_adapter_projection":"mocked CaptureBundle dataclass with synthetic labels",
            "raw":binding(cls.raw), "human_signoff":False,
        })
        cls.vfr = cls.bundle_root / "synthetic-vfr36.mkv"
        run_command(CommandSpec.create([
            FFMPEG, "-nostdin", "-hide_banner", "-loglevel", "warning", "-n",
            "-f", "lavfi", "-i", "nullsrc=size=64x64:rate=60:duration=2",
            "-vf", "geq=lum='N*2+8':cb=128:cr=128,select='lt(mod(n,10),3)+eq(mod(n,10),4)+eq(mod(n,10),5)+eq(mod(n,10),7)'",
            "-fps_mode", "passthrough", "-c:v", "ffv1", cls.vfr,
        ], label="synthetic VFR timestamp and grayscale fixture, not CK3", partial_artifacts=[cls.vfr]),
            audit_directory=ARTIFACT_ROOT / "synthetic-vfr-command")

    def test_spec_and_role_do_not_grant_causality(self):
        path = ARTIFACT_ROOT / "selection-spec.json"
        write_new(path, {"schema":cm.SPEC_SCHEMA,"clips":[self.spec]})
        self.assertEqual(cm.load_capture_spec(path), [self.spec])
        for change in ({"duration_seconds":float("nan")}, {"offset_seconds":-1},
                       {"claim_ids":["X","X"]}, {"evidence_role":"approved-native-cause"}):
            with self.subTest(change=change), self.assertRaises(cm.CaptureClipError):
                cm._clip_spec({**self.spec,**change})
        self.assertFalse((ARTIFACT_ROOT / "unused-output.mp4").exists())

    def test_window_is_inward_and_never_padded(self):
        span = self.bundle.clean_span("SYNTHETIC")
        window = cm._frame_window(span,{**self.spec,"offset_seconds":0.21,"duration_seconds":0.79},2)
        self.assertGreaterEqual(window["source_begin_seconds"],0.21)
        self.assertLessEqual(window["source_end_seconds"],1.0)
        self.assertLessEqual(0.79-window["expected_duration_seconds"],1/30)
        for change in ({"offset_seconds":1.9,"duration_seconds":0.2},
                       {"offset_seconds":0,"duration_seconds":0.01},
                       {"offset_seconds":0.001,"duration_seconds":0.097}):
            with self.subTest(change=change), self.assertRaises(cm.CaptureClipError):
                cm._frame_window(span,{**self.spec,**change},2)
        with self.assertRaises(cm.CaptureClipError):
            cm._require_30fps({"r_frame_rate":"25/1","avg_frame_rate":"25/1"})

    def test_actual_adapter_rejects_red_and_preserves_failure(self):
        root = ARTIFACT_ROOT / "explicit-red-source"
        root.mkdir()
        write_new(root / "report.json",{"schema_version":1,"result":"RED","cell":{"schema_version":1,"result":"RED"}})
        write_new(root / "cell/promo/capture-timeline.json",{})
        write_new(root / "evidence-index.json",{})
        destination = ARTIFACT_ROOT / "red-output.mp4"
        audit = ARTIFACT_ROOT / "red-audit"
        with self.assertRaises(CK3CaptureError):
            cm.prepare_capture_clip({**self.spec,"bundle_root":root.as_posix()},destination,FFMPEG,FFPROBE,audit)
        self.assertEqual(load(audit / "failure.json")["status"],"failed-retained")
        self.assertFalse(destination.exists())
        self.assertFalse((audit / "encode").exists())
        self.assertEqual(load(root / "report.json")["result"],"RED")

    def test_real_media_roundtrip_with_explicitly_mocked_synthetic_bundle(self):
        destination = ARTIFACT_ROOT / "synthetic-prepared.mp4"
        audit = ARTIFACT_ROOT / "synthetic-prepared-audit"
        old_files = {path:binding(path) for path in self.bundle_root.iterdir() if path.is_file()}
        with patch.object(cm,"load_capture_bundle",return_value=self.bundle) as adapter:
            result = cm.prepare_capture_clip(self.spec,destination,FFMPEG,FFPROBE,audit)
        adapter.assert_called_once_with(self.bundle_root,required_span_ids=["SYNTHETIC"])
        self.assertEqual(result["frame_check"]["decoded_frame_count"],24)
        self.assertAlmostEqual(result["duration_seconds"],0.8,places=3)
        self.assertFalse(result["source_audio_included"])
        self.assertFalse(result["native_ai_causality_verified"])
        self.assertIn("synthetic",result["source_kind"])
        self.assertEqual(result["media"],binding(destination))
        self.assertEqual(result["source_recording"]["path"],self.raw.as_posix())
        self.assertEqual(len(result["controls"]),4)
        for item in result["controls"]:
            self.assertEqual(item["preserved"],binding(item["preserved"]["path"]))
            self.assertEqual(item["preserved"]["sha256"],item["source"]["sha256"])
        for path, expected in old_files.items():
            self.assertEqual(binding(path),expected)
        command = load(audit / "encode/command.json")["argv"]
        self.assertNotIn("-r",command)
        self.assertNotIn("-stream_loop",command)
        self.assertNotIn("tpad",command[command.index("-vf")+1])
        before = binding(destination)
        with self.assertRaises(FileExistsError):
            cm.prepare_capture_clip(self.spec,destination,FFMPEG,FFPROBE,audit)
        self.assertEqual(binding(destination),before)

    def test_mutation_after_render_retains_partial_and_rejects(self):
        alternate = ARTIFACT_ROOT / "mutation-control.json"
        write_new(alternate,{"synthetic":True,"initial":True})
        altered_bundle = replace(self.bundle,report=capture_file(alternate,ARTIFACT_ROOT))
        original_run = cm.run_command
        def mutate_after_encode(command, **kwargs):
            result = original_run(command,**kwargs)
            if command.label == "prepare continuous CK3 capture clip":
                with alternate.open("ab") as stream:
                    stream.write(b"\n")
            return result
        audit = ARTIFACT_ROOT / "mutation-audit"
        destination = ARTIFACT_ROOT / "mutation-partial.mp4"
        with patch.object(cm,"load_capture_bundle",return_value=altered_bundle), patch.object(cm,"run_command",side_effect=mutate_after_encode):
            with self.assertRaises(CK3CaptureError):
                cm.prepare_capture_clip(self.spec,destination,FFMPEG,FFPROBE,audit)
        failure = load(audit / "failure.json")
        self.assertEqual(failure["status"],"failed-retained")
        self.assertEqual(failure["partial_media"],binding(destination))
        self.assertFalse((audit / "receipt.json").exists())
        self.assertTrue((audit / "encode/command.json").exists())

    def test_actual_vfr_keeps_1x_and_samples_previous_not_future_frame(self):
        source = replace(self.bundle, raw_capture=capture_file(self.vfr, self.bundle_root))
        target, audit = ARTIFACT_ROOT / "vfr-prepared.mp4", ARTIFACT_ROOT / "vfr-audit"
        with patch.object(cm, "load_capture_bundle", return_value=source):
            receipt = cm.prepare_capture_clip(self.spec, target, FFMPEG, FFPROBE, audit)
        self.assertAlmostEqual(receipt["duration_seconds"], .8, places=3)
        self.assertEqual(receipt["frame_check"]["decoded_frame_count"], 24)
        quality = receipt["source_sampling_quality"]
        self.assertFalse(quality["contiguous_zero_based_30fps"])
        self.assertGreater(quality["mean_observed_frame_rate"], 30)
        self.assertGreater(quality["maximum_gap_seconds"], 1/30)
        self.assertEqual(receipt["delivery_sampling"]["playback_speed"], 1)
        self.assertFalse(receipt["delivery_sampling"]["interpolation"])
        self.assertFalse(receipt["delivery_sampling"]["tail_padding"])
        sample = load(receipt["display_sampling"]["path"])
        self.assertTrue(all(row["source_pts_seconds"] <= row["source_time_seconds"] + 1e-10
                            for row in sample["mapping"]))
        decoded = []
        for name, video in (("source", self.vfr), ("output", target)):
            pixels = ARTIFACT_ROOT / f"vfr-{name}-gray.bin"
            run_command(CommandSpec.create([
                FFMPEG, "-nostdin", "-hide_banner", "-loglevel", "warning", "-n",
                "-i", video, "-map", "0:v:0", "-vf", "crop=2:2:(iw-2)/2:(ih-2)/2,format=gray",
                "-fps_mode", "passthrough", "-f", "rawvideo", pixels,
            ], label=f"synthetic VFR {name} pixel-time verification", partial_artifacts=[pixels]),
                audit_directory=ARTIFACT_ROOT / f"vfr-{name}-pixel-audit")
            raw_pixels = pixels.read_bytes()
            self.assertEqual(len(raw_pixels) % 4, 0)
            decoded.append([sum(raw_pixels[index:index+4])/4 for index in range(0, len(raw_pixels), 4)])
        original, delivered = decoded
        self.assertEqual(len(delivered), len(sample["mapping"]))
        for row, pixel in zip(sample["mapping"], delivered):
            self.assertLessEqual(abs(pixel-original[row["source_decoded_index"]]), 2,
                f"output frame {row['output_frame']} displayed a source frame outside the current-frame mapping")
        self.assertFalse(receipt["native_ai_causality_verified"])
        self.assertFalse(receipt["human_1x_review_performed"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root",type=Path,required=True)
    parser.add_argument("--ffmpeg",default="ffmpeg")
    parser.add_argument("--ffprobe",default="ffprobe")
    args, remaining = parser.parse_known_args()
    ARTIFACT_ROOT = args.artifact_root.resolve()
    ARTIFACT_ROOT.mkdir(parents=True,exist_ok=False)
    FFMPEG, FFPROBE = args.ffmpeg,args.ffprobe
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CaptureMediaTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    write_new(ARTIFACT_ROOT / "test-result.json",{
        "schema":"ck3-war-ai.capture-import-synthetic-check.v1",
        "created_at_utc":datetime.now(timezone.utc).isoformat(),
        "result":"PASS" if result.wasSuccessful() else "FAIL", "tests":result.testsRun,
        "failures":[{"test":str(test),"traceback":trace} for test,trace in result.failures],
        "errors":[{"test":str(test),"traceback":trace} for test,trace in result.errors],
        "synthetic_only":True,"ck3_started":False,"green_ck3_bundle_tested":False,
        "human_1x_review_performed":False,"signoff_granted":False,
    })
    sys.exit(0 if result.wasSuccessful() else 1)
