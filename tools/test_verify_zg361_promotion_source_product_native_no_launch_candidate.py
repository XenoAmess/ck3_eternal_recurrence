#!/usr/bin/env python3
"""Focused tests for the product/native dual-build no-launch freeze."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import verify_zg361_promotion_source_product_native_no_launch_candidate as verifier


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / (
    "ck3_autonomous_player/native_bridge/research/fixtures/"
    "zhongguo_promotion_source_product_native_no_launch_candidate_"
    "1c69658_20260904.json"
)


class ProductNativeNoLaunchCandidateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def verify(self, manifest: dict[str, object]) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "candidate.json"
            path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return verifier.verify_product_native_no_launch_candidate(
                path, source_root=ROOT, running_process_names=[]
            )

    def test_dual_build_candidate_is_ready_for_serial_live(self) -> None:
        report = self.verify(self.manifest)
        self.assertEqual(report["result"], "READY_TO_SERIAL_LIVE")
        self.assertEqual(report["failed_checks"], [])
        self.assertFalse(report["ck3_started"])
        self.assertFalse(report["live_proof_claimed"])
        self.assertFalse(report["production_advertisement_ready"])

    def test_rejects_product_aggregate_drift(self) -> None:
        with patch.object(
            verifier,
            "_product_source_fingerprint",
            return_value=("0" * 64, 975, 81920855),
        ):
            report = self.verify(self.manifest)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(report["checks"]["tracked_product_source_exact"])

    def test_rejects_default_or_candidate_flag_conflation(self) -> None:
        changed = copy.deepcopy(self.manifest)
        flag = verifier.COMPENSATION_FLAG
        changed["build"]["capability_flags"][flag] = "ON"
        changed["build_boundary"]["candidate_flag_is_default"] = True
        report = self.verify(changed)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(report["checks"]["default_cache_all_private_flags_off"])
        self.assertFalse(
            report["checks"]["default_and_candidate_semantics_not_conflated"]
        )

    def test_rejects_candidate_binary_or_command_drift(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["live_candidate_build"]["bridge"]["sha256"] = "0" * 64
        changed["live_command"]["argv"].append("--unexpected")
        report = self.verify(changed)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(
            report["checks"]["fresh_compensation_on_build_and_ctest_exact"]
        )
        self.assertFalse(
            report["checks"]["single_future_command_uses_candidate_only_build"]
        )

    def test_rejects_false_live_or_production_claim(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["live_proof_claimed"] = True
        changed["production_advertisement_ready"] = True
        report = self.verify(changed)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(report["checks"]["no_launch_or_ack_result_claim"])


if __name__ == "__main__":
    unittest.main()
