"""Focused fail-closed checks for the real Episode 2 source declaration."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE = Path(__file__).with_name("prepare_production_inputs.py")
SPEC = importlib.util.spec_from_file_location("episode02_production_preflight", MODULE)
assert SPEC and SPEC.loader
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


class ProductionPreflightTests(unittest.TestCase):
    def test_original_sha_change_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            source.write_text("first\n", encoding="utf-8")
            binding = {"source": str(source), **preflight.identity(source)}
            self.assertEqual(preflight._source(binding, "source")[0], source.resolve())
            source.write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "bytes/SHA differ"):
                preflight._source(binding, "source")

    def test_unreviewed_clean_span_rejected_before_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = {}
            for artifact_id in ("save", "raw", "control", "clean", "label", "frame",
                                "probe", "recorder"):
                path = root / artifact_id
                if artifact_id == "clean":
                    path.write_text(json.dumps({"result": "RED", "span_id": "not-reviewed"}), encoding="utf-8")
                elif artifact_id == "label":
                    path.write_text(json.dumps({"frame_artifact_id": "frame"}), encoding="utf-8")
                else:
                    path.write_bytes(artifact_id.encode())
                original[artifact_id] = (path, {"artifact_id": artifact_id, **preflight.identity(path)})
            span = {"attempt_id": "E2-09-a05",
                    "cold_load_save_artifact_id": "save", "raw_video_artifact_id": "raw",
                    "control_artifact_id": "control", "clean_span_receipt_artifact_id": "clean",
                    "label_audit_artifact_id": "label",
                    "raw_video_pts_probe_artifact_id": "probe",
                    "raw_video_recorder_final_artifact_id": "recorder",
                    "raw_video_width": 1920, "raw_video_height": 1080,
                    "upscaled_to_reel": True, "resampled_to_reel": True}
            for field, artifact_id in (("cold_load_save", "save"), ("raw_video", "raw"),
                                       ("control", "control")):
                span[f"{field}_sha256"] = original[artifact_id][1]["sha256"]
                span[f"{field}_bytes"] = original[artifact_id][1]["bytes"]
            with self.assertRaisesRegex(ValueError, "lacks a GREEN clean span"):
                preflight._capture_source_gate(span, original, "A" * 64, 60)

    def test_synthetic_declaration_cannot_enter_real_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "declaration.json"
            path.write_text(json.dumps({
                "schema": "ck3-war-ai.episode02.production-declaration.v1",
                "human_signoff": "not-provided", "synthetic": True,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-synthetic"):
                preflight.prepare(path)


if __name__ == "__main__":
    unittest.main()
